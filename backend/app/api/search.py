from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, desc
from app.database import get_db
from app.models import Form4Filing, Filing13DG

router = APIRouter()


@router.get("/")
def search(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """
    Unified search across tickers and insider names.
    Returns matching tickers (companies) and insider names.
    """
    term = q.strip().upper()
    like_term = f"%{term}%"

    # Ticker matches
    tickers = (
        db.query(
            Form4Filing.ticker,
            Form4Filing.company_name,
            func.count(Form4Filing.id).label("filing_count"),
        )
        .filter(
            or_(
                Form4Filing.ticker.ilike(like_term),
                Form4Filing.company_name.ilike(like_term),
            )
        )
        .group_by(Form4Filing.ticker, Form4Filing.company_name)
        .order_by(desc("filing_count"))
        .limit(10)
        .all()
    )

    # Insider name matches
    insiders = (
        db.query(
            Form4Filing.insider_cik,
            Form4Filing.insider_name,
            func.count(Form4Filing.id).label("filing_count"),
        )
        .filter(Form4Filing.insider_name.ilike(like_term))
        .group_by(Form4Filing.insider_cik, Form4Filing.insider_name)
        .order_by(desc("filing_count"))
        .limit(10)
        .all()
    )

    return {
        "query": q,
        "tickers": [
            {"ticker": r.ticker, "company_name": r.company_name, "filing_count": r.filing_count}
            for r in tickers
        ],
        "insiders": [
            {"insider_cik": r.insider_cik, "insider_name": r.insider_name, "filing_count": r.filing_count}
            for r in insiders
        ],
    }
