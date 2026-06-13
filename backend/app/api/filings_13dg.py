from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import date, timedelta

from app.database import get_db
from app.models import Filing13DG

router = APIRouter()


@router.get("/feed")
def get_13dg_feed(
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=200),
    form_type: Optional[str] = None,
    ticker: Optional[str] = None,
    filer: Optional[str] = None,
    days: int = Query(90),
    db: Session = Depends(get_db),
):
    cutoff = date.today() - timedelta(days=days)
    q = db.query(Filing13DG).filter(Filing13DG.filing_date >= cutoff)

    if form_type:
        q = q.filter(Filing13DG.form_type.ilike(f"%{form_type}%"))
    if ticker:
        q = q.filter(Filing13DG.subject_ticker == ticker.upper())
    if filer:
        q = q.filter(Filing13DG.filer_name.ilike(f"%{filer}%"))

    total = q.count()
    items = (
        q.order_by(desc(Filing13DG.filing_date))
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return {"total": total, "page": page, "limit": limit, "items": items}


@router.get("/company/{ticker}")
def get_company_13dg(ticker: str, days: int = Query(365 * 3), db: Session = Depends(get_db)):
    cutoff = date.today() - timedelta(days=days)
    filings = (
        db.query(Filing13DG)
        .filter(
            Filing13DG.subject_ticker == ticker.upper(),
            Filing13DG.filing_date >= cutoff,
        )
        .order_by(desc(Filing13DG.filing_date))
        .all()
    )
    return {"ticker": ticker.upper(), "filings": filings}


@router.get("/filer/{filer_cik}")
def get_filer_history(filer_cik: str, db: Session = Depends(get_db)):
    filings = (
        db.query(Filing13DG)
        .filter(Filing13DG.filer_cik == filer_cik)
        .order_by(desc(Filing13DG.filing_date))
        .all()
    )
    filer_name = filings[0].filer_name if filings else "Unknown"
    return {"filer_cik": filer_cik, "filer_name": filer_name, "filings": filings}
