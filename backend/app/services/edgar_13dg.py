"""
EDGAR 13D / 13G ingestion service.

Handles: SC 13D, SC 13D/A, SC 13G, SC 13G/A filings.
These reveal investors who cross the 5% ownership threshold.
"""

import re
import logging
import time
from datetime import datetime, date
from typing import Optional

import httpx
from lxml import etree, html
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.models import Filing13DG
from app.database import SessionLocal

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "SecInsiderTracker ranjittotest@gmail.com",  # CHANGE THIS
    "Accept-Encoding": "gzip, deflate",
}

BASE_URL = "https://www.sec.gov"


def _get(url: str, retries: int = 3) -> Optional[httpx.Response]:
    for attempt in range(retries):
        try:
            resp = httpx.get(url, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                return resp
            if resp.status_code == 429:
                time.sleep(10 * (attempt + 1))
                continue
        except Exception as e:
            logger.error(f"Request error ({attempt+1}/{retries}): {e}")
            time.sleep(5)
    return None


def fetch_recent_13dg_accessions(count: int = 40) -> list[dict]:
    """
    Fetch the most recent 13D/13G filings from EDGAR.
    Queries for SC 13D and SC 13G separately.
    """
    accessions = []
    for form_type in ["SC+13D", "SC+13G"]:
        url = f"{BASE_URL}/cgi-bin/browse-edgar?action=getcurrent&type={form_type}&dateb=&owner=include&count={count}&output=atom"
        resp = _get(url)
        if not resp:
            continue

        try:
            root = etree.fromstring(resp.content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns):
                link_el = entry.find("atom:link", ns)
                if link_el is None:
                    continue
                accession_url = link_el.get("href", "")
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
                    title_el = entry.find("atom:title", ns)
                    title_text = title_el.text if title_el is not None else ""
                    # Detect amendment
                    actual_form_type = "SC 13D/A" if "13D/A" in title_text else \
                                       "SC 13G/A" if "13G/A" in title_text else \
                                       "SC 13D" if "13D" in title_text else "SC 13G"
                    accessions.append({
                        "accession_number": accession,
                        "filer_cik": cik,
                        "form_type": actual_form_type,
                        "filing_date": filing_date,
                    })
        except Exception as e:
            logger.error(f"Error parsing 13DG RSS for {form_type}: {e}")

    return accessions


def fetch_13dg_filing_details(filer_cik: str, accession_number: str, form_type: str) -> Optional[dict]:
    """
    Parse the 13D/13G filing index page to extract:
    - Subject company CIK, ticker, name
    - Filer name
    - Percent owned
    - Shares owned
    - Event date
    """
    clean = accession_number.replace("-", "")
    index_url = f"{BASE_URL}/Archives/edgar/data/{filer_cik}/{clean}/{accession_number}-index.htm"
    resp = _get(index_url)
    if not resp:
        return None

    details = {
        "form_type": form_type,
        "filer_cik": filer_cik,
        "accession_number": accession_number,
        "form_url": index_url,
    }

    # Parse HTML index for subject company info
    try:
        tree = html.fromstring(resp.content)

        # Subject company name and CIK are in the index header
        subject_name_els = tree.xpath('//td[contains(@class,"formContent")]//span[@class="companyName"]')
        if subject_name_els:
            subject_text = subject_name_els[0].text_content()
            name_match = re.match(r"(.+?)\s+\(CIK", subject_text)
            if name_match:
                details["subject_company"] = name_match.group(1).strip()
            cik_match = re.search(r"CIK\s+(\d+)", subject_text)
            if cik_match:
                details["subject_cik"] = cik_match.group(1)

        # Try to get filer name
        filer_els = tree.xpath('//td[contains(text(),"Filed by")]/../td[2]')
        if filer_els:
            details["filer_name"] = filer_els[0].text_content().strip()

    except Exception as e:
        logger.warning(f"HTML parse warning for {accession_number}: {e}")

    # Try to get subject ticker from EDGAR company lookup
    if details.get("subject_cik"):
        ticker = _lookup_ticker(details["subject_cik"])
        if ticker:
            details["subject_ticker"] = ticker

    # Try to parse the actual document for percent/shares
    doc_details = _parse_13dg_document(filer_cik, clean, accession_number)
    if doc_details:
        details.update(doc_details)

    return details


def _parse_13dg_document(cik: str, clean_accession: str, accession_number: str) -> Optional[dict]:
    """
    Attempt to extract percent_owned, shares_owned, and event_date
    from the primary 13D/13G document (text or XML).
    """
    # First check for an XML version
    xml_url = f"{BASE_URL}/Archives/edgar/data/{cik}/{clean_accession}/primary-document.xml"
    resp = _get(xml_url)

    if resp and resp.status_code == 200:
        try:
            root = etree.fromstring(resp.content)
            def text(node, path, default=""):
                el = node.find(path)
                return el.text.strip() if el is not None and el.text else default

            pct = text(root, ".//percentOfClass")
            shares = text(root, ".//amountBeneficiallyOwned")
            event_date_str = text(root, ".//dateOfEventWhichRequiresFiling")
            event_date = None
            if event_date_str:
                try:
                    event_date = date.fromisoformat(event_date_str)
                except Exception:
                    pass

            result = {}
            if pct:
                try:
                    result["percent_owned"] = float(pct.replace("%", "").strip())
                except ValueError:
                    pass
            if shares:
                try:
                    result["shares_owned"] = int(shares.replace(",", "").strip())
                except ValueError:
                    pass
            if event_date:
                result["event_date"] = event_date
            return result if result else None
        except Exception:
            pass

    # Fallback: fetch the text document and regex-parse key fields
    # List documents from index
    index_url = f"{BASE_URL}/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=SC+13&dateb=&owner=include&count=1&search_text="
    return None  # Acceptable fallback — percent/shares will be null


def _lookup_ticker(cik: str) -> Optional[str]:
    """Look up ticker symbol from EDGAR company submissions API."""
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    resp = _get(url)
    if not resp:
        return None
    try:
        data = resp.json()
        tickers = data.get("tickers", [])
        return tickers[0].upper() if tickers else None
    except Exception:
        return None


def upsert_13dg_records(records: list[dict], db: Session) -> int:
    if not records:
        return 0
    stmt = (
        insert(Filing13DG)
        .values(records)
        .on_conflict_do_nothing(index_elements=["accession_number"])
    )
    result = db.execute(stmt)
    db.commit()
    return result.rowcount


def ingest_recent_13dg() -> int:
    db = SessionLocal()
    total_inserted = 0
    try:
        accessions = fetch_recent_13dg_accessions(count=40)
        for item in accessions:
            existing = db.query(Filing13DG).filter_by(accession_number=item["accession_number"]).first()
            if existing:
                continue
            time.sleep(0.15)
            details = fetch_13dg_filing_details(item["filer_cik"], item["accession_number"], item["form_type"])
            if not details:
                continue
            # Merge filing_date from RSS
            details["filing_date"] = item["filing_date"]
            inserted = upsert_13dg_records([details], db)
            total_inserted += inserted
            logger.info(f"Inserted 13DG: {item['accession_number']} ({item['form_type']})")
    except Exception as e:
        logger.error(f"13DG ingest error: {e}")
    finally:
        db.close()
    return total_inserted
