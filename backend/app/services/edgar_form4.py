"""
EDGAR Form 4 ingestion service.

Flow:
  1. Poll EDGAR's current-filing RSS feed for new Form 4 accession numbers
  2. For each unseen accession, fetch the filing index to locate the XML document
  3. Parse the XML into Form4Filing records and upsert into PostgreSQL
  4. Backfill uses the EDGAR full-index files (company.idx per quarter)
"""

import re
import logging
import time
from datetime import datetime, date
from typing import Optional

import httpx
from lxml import etree
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.models import Form4Filing
from app.database import SessionLocal

logger = logging.getLogger(__name__)

# SEC requires a descriptive User-Agent header — without it you get 403s
HEADERS = {
    "User-Agent": "SecInsiderTracker ranjittotest@gmail.com",  # CHANGE THIS
    "Accept-Encoding": "gzip, deflate",
}

BASE_URL = "https://www.sec.gov"
EDGAR_DATA = "https://data.sec.gov"

# Transaction code mapping
TXN_CODE_LABELS = {
    "P": "Purchase",
    "S": "Sale",
    "A": "Award / Grant",
    "D": "Disposition (non-sale)",
    "F": "Tax Withholding",
    "G": "Gift",
    "I": "Discretionary Transaction",
    "M": "Option Exercise",
    "X": "Option Exercise (expired)",
    "C": "Conversion",
    "E": "Expiration",
    "H": "Expiration (in-the-money)",
    "O": "Exercise of out-of-the-money",
    "U": "Tender",
    "W": "Acquisition by Will",
    "Z": "Voting Trust",
}


def _get(url: str, retries: int = 3) -> Optional[httpx.Response]:
    """Rate-limited GET with retry on 429/5xx."""
    for attempt in range(retries):
        try:
            resp = httpx.get(url, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                return resp
            if resp.status_code == 429:
                time.sleep(10 * (attempt + 1))
                continue
            logger.warning(f"HTTP {resp.status_code} for {url}")
            return None
        except Exception as e:
            logger.error(f"Request error ({attempt+1}/{retries}): {e}")
            time.sleep(5)
    return None


def fetch_recent_form4_accessions(count: int = 40) -> list[dict]:
    """
    Returns list of {accession_number, cik, company_name, filing_date}
    from the EDGAR current-filings feed filtered to Form 4.
    """
    url = f"{BASE_URL}/cgi-bin/browse-edgar?action=getcurrent&type=4&dateb=&owner=include&count={count}&output=atom"
    resp = _get(url)
    if not resp:
        return []

    accessions = []
    try:
        root = etree.fromstring(resp.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns):
            accession_url = entry.find("atom:link", ns).get("href", "")
            # Extract accession number from URL
            m = re.search(r"/Archives/edgar/data/(\d+)/(\d{18})", accession_url)
            if m:
                cik = m.group(1)
                raw = m.group(2)
                accession = f"{raw[:10]}-{raw[10:12]}-{raw[12:]}"
                updated = entry.find("atom:updated", ns)
                filing_date = None
                if updated is not None:
                    try:
                        filing_date = datetime.fromisoformat(updated.text.replace("Z", "+00:00"))
                    except Exception:
                        pass
                title = entry.find("atom:title", ns)
                company_name = title.text.split("(")[0].strip() if title is not None else ""
                accessions.append({
                    "accession_number": accession,
                    "cik": cik,
                    "company_name": company_name,
                    "filing_date": filing_date,
                })
    except Exception as e:
        logger.error(f"Error parsing EDGAR RSS: {e}")

    return accessions


def fetch_filing_xml_url(cik: str, accession_number: str) -> Optional[str]:
    """
    Fetch the filing index page and return the URL of the primary Form 4 XML file.
    """
    clean_accession = accession_number.replace("-", "")
    index_url = f"{BASE_URL}/Archives/edgar/data/{cik}/{clean_accession}/{accession_number}-index.htm"
    resp = _get(index_url)
    if not resp:
        return None

    # Look for the _doc.xml or primary XML document
    xml_pattern = re.compile(r'href="(/Archives/edgar/data/\d+/[^"]+\.xml)"', re.IGNORECASE)
    matches = xml_pattern.findall(resp.text)

    # Prefer files that look like primary Form 4 XML (not _cal.xml, _lab.xml, etc.)
    primary_candidates = [m for m in matches if not any(x in m for x in ["_cal", "_lab", "_pre", "_def", "R1", "R2"])]
    if primary_candidates:
        return BASE_URL + primary_candidates[0]

    # Fallback: try standard naming convention
    accession_nodash = accession_number.replace("-", "")
    return f"{BASE_URL}/Archives/edgar/data/{cik}/{accession_nodash}/{accession_nodash}.xml"


def parse_form4_xml(xml_content: bytes, cik: str, accession_number: str, filing_date: Optional[datetime]) -> list[dict]:
    """
    Parse Form 4 XML and return list of transaction dicts.
    Each non-derivative and derivative transaction becomes one record.
    """
    records = []
    try:
        root = etree.fromstring(xml_content)
    except Exception as e:
        logger.error(f"XML parse error for {accession_number}: {e}")
        return []

    def text(node, path, default=""):
        el = node.find(path)
        return el.text.strip() if el is not None and el.text else default

    def numtext(node, path, default=None):
        val = text(node, path)
        if not val:
            return default
        try:
            return float(val.replace(",", ""))
        except ValueError:
            return default

    # Issuer info
    issuer_cik = text(root, ".//issuerCik") or cik
    ticker = text(root, ".//issuerTradingSymbol").upper()
    company_name = text(root, ".//issuerName")

    # Owner info
    insider_cik = text(root, ".//rptOwnerCik")
    insider_name = text(root, ".//rptOwnerName")
    is_director = text(root, ".//isDirector", "0")
    is_officer = text(root, ".//isOfficer", "0")
    is_ten_pct = text(root, ".//isTenPercentOwner", "0")
    officer_title = text(root, ".//officerTitle")

    common_fields = {
        "accession_number": accession_number,
        "issuer_cik": issuer_cik,
        "ticker": ticker,
        "company_name": company_name,
        "insider_cik": insider_cik,
        "insider_name": insider_name,
        "is_director": is_director,
        "is_officer": is_officer,
        "is_ten_pct_owner": is_ten_pct,
        "officer_title": officer_title,
        "filing_date": filing_date,
        "form_url": f"{BASE_URL}/Archives/edgar/data/{cik}/{accession_number.replace('-', '')}/{accession_number}-index.htm",
        "is_derivative": "N",
    }

    # Non-derivative transactions
    for txn in root.findall(".//nonDerivativeTransaction"):
        txn_date_str = text(txn, "transactionDate/value")
        try:
            txn_date = date.fromisoformat(txn_date_str)
        except Exception:
            txn_date = None

        shares = numtext(txn, "transactionAmounts/transactionShares/value")
        price = numtext(txn, "transactionAmounts/transactionPricePerShare/value", 0.0)
        txn_code = text(txn, "transactionAmounts/transactionCode/value")
        acq_disp = text(txn, "transactionAmounts/transactionAcquiredDisposedCode/value")
        shares_after = numtext(txn, "postTransactionAmounts/sharesOwnedFollowingTransaction/value")
        direct = text(txn, "ownershipNature/directOrIndirectOwnership/value", "D")
        security_title = text(txn, "securityTitle/value")

        total_value = (shares or 0) * (price or 0) if shares else None

        record = {
            **common_fields,
            "txn_date": txn_date,
            "shares": shares,
            "price_per_share": price,
            "total_value": total_value,
            "txn_code": txn_code,
            "txn_type": acq_disp,
            "is_direct": direct,
            "shares_owned_after": shares_after,
            "security_title": security_title,
        }
        records.append(record)

    # Derivative transactions (options, warrants, etc.)
    for txn in root.findall(".//derivativeTransaction"):
        txn_date_str = text(txn, "transactionDate/value")
        try:
            txn_date = date.fromisoformat(txn_date_str)
        except Exception:
            txn_date = None

        shares = numtext(txn, "transactionAmounts/transactionShares/value")
        price = numtext(txn, "transactionAmounts/transactionPricePerShare/value", 0.0)
        txn_code = text(txn, "transactionAmounts/transactionCode/value")
        acq_disp = text(txn, "transactionAmounts/transactionAcquiredDisposedCode/value")
        security_title = text(txn, "securityTitle/value")

        record = {
            **common_fields,
            "is_derivative": "Y",
            "txn_date": txn_date,
            "shares": shares,
            "price_per_share": price,
            "total_value": None,
            "txn_code": txn_code,
            "txn_type": acq_disp,
            "is_direct": "D",
            "shares_owned_after": None,
            "security_title": security_title,
        }
        records.append(record)

    return records


def upsert_form4_records(records: list[dict], db: Session) -> int:
    """Upsert records into form4_filings, skip on accession_number conflict."""
    if not records:
        return 0
    stmt = (
        insert(Form4Filing)
        .values(records)
        .on_conflict_do_nothing(index_elements=["accession_number"])
    )
    result = db.execute(stmt)
    db.commit()
    return result.rowcount


def ingest_recent_filings() -> int:
    """Pull latest Form 4s from EDGAR and save new ones. Returns count inserted."""
    db = SessionLocal()
    total_inserted = 0
    try:
        accessions = fetch_recent_form4_accessions(count=40)
        for item in accessions:
            # Skip if already ingested
            existing = db.query(Form4Filing).filter_by(accession_number=item["accession_number"]).first()
            if existing:
                continue

            xml_url = fetch_filing_xml_url(item["cik"], item["accession_number"])
            if not xml_url:
                continue

            time.sleep(0.12)  # Stay under SEC's 10 req/sec limit
            resp = _get(xml_url)
            if not resp:
                continue

            records = parse_form4_xml(resp.content, item["cik"], item["accession_number"], item["filing_date"])
            inserted = upsert_form4_records(records, db)
            total_inserted += inserted
            logger.info(f"Inserted {inserted} records from {item['accession_number']}")

    except Exception as e:
        logger.error(f"Ingest error: {e}")
    finally:
        db.close()

    return total_inserted
