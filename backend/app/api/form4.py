from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from typing import Optional
from datetime import date, timedelta

from app.database import get_db
from app.models import Form4Filing
from app.schemas import Form4Row, PaginatedForm4, BuySellSummary

router = APIRouter()


@router.get("/feed", response_model=PaginatedForm4)
def get_feed(
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=200),
    txn_type: Optional[str] = Query(None, description="A=Buy, D=Sell"),
    ticker: Optional[str] = None,
    min_value: Optional[float] = None,
    days: int = Query(30, description="Look-back window in days"),
    exclude_derivatives: bool = True,
    db: Session = Depends(get_db),
):
    q = db.query(Form4Filing)
    cutoff = date.today() - timedelta(days=days)
    q = q.filter(Form4Filing.txn_date >= cutoff)

    if exclude_derivatives:
        q = q.filter(Form4Filing.is_derivative == "N")
    if txn_type:
        q = q.filter(Form4Filing.txn_type == txn_type.upper())
    if ticker:
        q = q.filter(Form4Filing.ticker == ticker.upper())
    if min_value is not None:
        q = q.filter(Form4Filing.total_value >= min_value)

    total = q.count()
    items = (
        q.order_by(desc(Form4Filing.filing_date))
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return {"total": total, "page": page, "limit": limit, "items": items}


@router.get("/company/{ticker}")
def get_company_filings(
    ticker: str,
    days: int = Query(365),
    exclude_derivatives: bool = True,
    db: Session = Depends(get_db),
):
    cutoff = date.today() - timedelta(days=days)
    q = (
        db.query(Form4Filing)
        .filter(
            Form4Filing.ticker == ticker.upper(),
            Form4Filing.txn_date >= cutoff,
        )
        .order_by(desc(Form4Filing.txn_date))
    )
    if exclude_derivatives:
        q = q.filter(Form4Filing.is_derivative == "N")
    filings = q.all()

    # Summary stats
    buys = [f for f in filings if f.txn_type == "A"]
    sells = [f for f in filings if f.txn_type == "D"]
    buy_value = sum(float(f.total_value or 0) for f in buys)
    sell_value = sum(float(f.total_value or 0) for f in sells)

    return {
        "ticker": ticker.upper(),
        "company_name": filings[0].company_name if filings else None,
        "summary": {
            "total_filings": len(filings),
            "buy_count": len(buys),
            "sell_count": len(sells),
            "buy_value": buy_value,
            "sell_value": sell_value,
            "net_value": buy_value - sell_value,
        },
        "filings": filings,
    }


@router.get("/insider/{insider_cik}")
def get_insider_filings(
    insider_cik: str,
    days: int = Query(365 * 3),
    db: Session = Depends(get_db),
):
    cutoff = date.today() - timedelta(days=days)
    filings = (
        db.query(Form4Filing)
        .filter(
            Form4Filing.insider_cik == insider_cik,
            Form4Filing.txn_date >= cutoff,
            Form4Filing.is_derivative == "N",
        )
        .order_by(desc(Form4Filing.txn_date))
        .all()
    )
    insider_name = filings[0].insider_name if filings else "Unknown"
    return {
        "insider_cik": insider_cik,
        "insider_name": insider_name,
        "filings": filings,
    }


@router.get("/cluster-buys")
def get_cluster_buys(
    days: int = Query(7, description="Window to detect multiple insiders buying same stock"),
    min_insiders: int = Query(2),
    min_value: float = Query(50000),
    db: Session = Depends(get_db),
):
    """Detect tickers where 2+ insiders bought within a short window — high-signal setup."""
    cutoff = date.today() - timedelta(days=days)
    results = (
        db.query(
            Form4Filing.ticker,
            Form4Filing.company_name,
            func.count(func.distinct(Form4Filing.insider_cik)).label("insider_count"),
            func.sum(Form4Filing.total_value).label("total_buy_value"),
            func.max(Form4Filing.txn_date).label("latest_buy"),
        )
        .filter(
            Form4Filing.txn_date >= cutoff,
            Form4Filing.txn_type == "A",
            Form4Filing.is_derivative == "N",
            Form4Filing.total_value >= min_value,
        )
        .group_by(Form4Filing.ticker, Form4Filing.company_name)
        .having(func.count(func.distinct(Form4Filing.insider_cik)) >= min_insiders)
        .order_by(desc("insider_count"))
        .limit(50)
        .all()
    )
    return [
        {
            "ticker": r.ticker,
            "company_name": r.company_name,
            "insider_count": r.insider_count,
            "total_buy_value": float(r.total_buy_value or 0),
            "latest_buy": r.latest_buy,
        }
        for r in results
    ]


@router.get("/buy-sell-ratio/{ticker}")
def buy_sell_ratio(ticker: str, days: int = Query(365), db: Session = Depends(get_db)):
    """Monthly buy vs sell dollar volume for chart rendering."""
    cutoff = date.today() - timedelta(days=days)
    results = (
        db.query(
            func.date_trunc("month", Form4Filing.txn_date).label("month"),
            Form4Filing.txn_type,
            func.sum(Form4Filing.total_value).label("volume"),
            func.count().label("count"),
        )
        .filter(
            Form4Filing.ticker == ticker.upper(),
            Form4Filing.txn_date >= cutoff,
            Form4Filing.is_derivative == "N",
        )
        .group_by("month", Form4Filing.txn_type)
        .order_by("month")
        .all()
    )
    monthly: dict = {}
    for r in results:
        key = r.month.strftime("%Y-%m") if r.month else "unknown"
        if key not in monthly:
            monthly[key] = {"month": key, "buy_volume": 0, "sell_volume": 0, "buy_count": 0, "sell_count": 0}
        if r.txn_type == "A":
            monthly[key]["buy_volume"] = float(r.volume or 0)
            monthly[key]["buy_count"] = r.count
        elif r.txn_type == "D":
            monthly[key]["sell_volume"] = float(r.volume or 0)
            monthly[key]["sell_count"] = r.count
    return list(monthly.values())
