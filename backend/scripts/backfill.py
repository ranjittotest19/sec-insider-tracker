"""
Historical backfill script.

Downloads EDGAR full-index files (company.idx) quarter by quarter from 2020
and ingests all Form 4, SC 13D, and SC 13G filings found.

Usage:
    python -m scripts.backfill --start 2020 --end 2025
    python -m scripts.backfill --start 2020 --end 2025 --form 4
    python -m scripts.backfill --start 2020 --end 2025 --form 13dg

This will take several hours for a full 5-year backfill.
Run it once after initial deployment. Use --workers to speed it up (careful
not to exceed SEC's rate limit of ~10 req/sec).
"""

import argparse
import logging
import time
import sys
import os

# Ensure the parent directory is on the path when run as a module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from sqlalchemy.dialects.postgresql import insert

from app.database import SessionLocal, engine
from app import models
from app.services.edgar_form4 import (
    fetch_filing_xml_url, parse_form4_xml, upsert_form4_records, HEADERS, _get
)
from app.services.edgar_13dg import (
    fetch_13dg_filing_details, upsert_13dg_records
)
from app.models import Form4Filing, Filing13DG

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.sec.gov"

FORM4_CODES = {"4", "4/A"}
THIRDDG_CODES = {"SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A"}


def fetch_quarter_index(year: int, quarter: int) -> list[dict]:
    """
    Download company.idx for a given year/quarter and return list of
    {form_type, company_name, cik, date_filed, filename} rows.
    """
    url = f"{BASE_URL}/Archives/edgar/full-index/{year}/QTR{quarter}/company.idx"
    logger.info(f"Fetching index: {url}")
    resp = _get(url)
    if not resp:
        logger.warning(f"Could not fetch {url}")
        return []

    entries = []
    lines = resp.text.splitlines()
    # Skip header lines (first 10 lines are headers/separator)
    for line in lines[10:]:
        if len(line) < 90:
            continue
        try:
            form_type = line[0:12].strip()
            company_name = line[12:62].strip()
            cik = line[62:74].strip()
            date_filed = line[74:84].strip()
            filename = line[84:].strip()
            entries.append({
                "form_type": form_type,
                "company_name": company_name,
                "cik": cik,
                "date_filed": date_filed,
                "filename": filename,
            })
        except Exception:
            continue
    return entries


def extract_accession_from_filename(filename: str) -> str:
    """Convert edgar filename like edgar/data/12345/0001234567-20-123456.txt to accession number."""
    basename = filename.split("/")[-1].replace(".txt", "")
    return basename


def backfill_form4_quarter(year: int, quarter: int, db) -> int:
    """Backfill all Form 4s for a given quarter."""
    entries = fetch_quarter_index(year, quarter)
    form4_entries = [e for e in entries if e["form_type"] in FORM4_CODES]
    logger.info(f"Q{quarter} {year}: found {len(form4_entries)} Form 4 entries")

    total = 0
    for i, entry in enumerate(form4_entries):
        accession_number = extract_accession_from_filename(entry["filename"])

        # Check if already ingested
        existing = db.query(Form4Filing).filter_by(accession_number=accession_number).first()
        if existing:
            continue

        try:
            from datetime import datetime
            filing_date = datetime.strptime(entry["date_filed"], "%Y-%m-%d") if entry["date_filed"] else None
        except ValueError:
            filing_date = None

        xml_url = fetch_filing_xml_url(entry["cik"], accession_number)
        if not xml_url:
            continue

        time.sleep(0.11)  # ~9 req/sec — under SEC limit
        resp = _get(xml_url)
        if not resp:
            continue

        records = parse_form4_xml(resp.content, entry["cik"], accession_number, filing_date)
        inserted = upsert_form4_records(records, db)
        total += inserted

        if (i + 1) % 100 == 0:
            logger.info(f"  Progress: {i+1}/{len(form4_entries)} processed, {total} records inserted")

    return total


def backfill_13dg_quarter(year: int, quarter: int, db) -> int:
    """Backfill all 13D/13G filings for a given quarter."""
    entries = fetch_quarter_index(year, quarter)
    dg_entries = [e for e in entries if e["form_type"] in THIRDDG_CODES]
    logger.info(f"Q{quarter} {year}: found {len(dg_entries)} 13D/13G entries")

    total = 0
    for i, entry in enumerate(dg_entries):
        accession_number = extract_accession_from_filename(entry["filename"])

        existing = db.query(Filing13DG).filter_by(accession_number=accession_number).first()
        if existing:
            continue

        try:
            from datetime import datetime
            filing_date = datetime.strptime(entry["date_filed"], "%Y-%m-%d") if entry["date_filed"] else None
        except ValueError:
            filing_date = None

        time.sleep(0.12)
        details = fetch_13dg_filing_details(entry["cik"], accession_number, entry["form_type"])
        if not details:
            continue
        details["filing_date"] = filing_date
        if not details.get("filer_name"):
            details["filer_name"] = entry["company_name"]

        inserted = upsert_13dg_records([details], db)
        total += inserted

        if (i + 1) % 50 == 0:
            logger.info(f"  Progress: {i+1}/{len(dg_entries)} processed, {total} records inserted")

    return total


def main():
    parser = argparse.ArgumentParser(description="Backfill SEC filings from EDGAR")
    parser.add_argument("--start", type=int, default=2020, help="Start year (default: 2020)")
    parser.add_argument("--end", type=int, default=2025, help="End year inclusive (default: 2025)")
    parser.add_argument("--form", choices=["4", "13dg", "all"], default="all", help="Which forms to backfill")
    parser.add_argument("--year", type=int, help="Process a single year only")
    parser.add_argument("--quarter", type=int, choices=[1, 2, 3, 4], help="Process a single quarter only")
    args = parser.parse_args()

    # Ensure tables exist
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        years = range(args.year, args.year + 1) if args.year else range(args.start, args.end + 1)
        quarters = [args.quarter] if args.quarter else [1, 2, 3, 4]

        grand_total = 0
        for year in years:
            for quarter in quarters:
                logger.info(f"=== Processing {year} Q{quarter} ===")
                if args.form in ("4", "all"):
                    n = backfill_form4_quarter(year, quarter, db)
                    logger.info(f"  Form 4: inserted {n} records")
                    grand_total += n
                if args.form in ("13dg", "all"):
                    n = backfill_13dg_quarter(year, quarter, db)
                    logger.info(f"  13D/13G: inserted {n} records")
                    grand_total += n

        logger.info(f"=== Backfill complete. Total records inserted: {grand_total} ===")
    finally:
        db.close()


if __name__ == "__main__":
    main()
