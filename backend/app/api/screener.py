from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from datetime import date, timedelta
from typing import Optional

from app.database import get_db
from app.models import Form4Filing, Filing13DG

router = APIRouter()


@router.get("/form4")
def screener(
    txn_type: Optional[str] = Query(None, description="A=Buy D=Sell"),
    min_value: float = Query(100000, description="Minimum transaction value"),
    max_value: Optional[float] = None,
    role: Optional[str] = Query(None, description="CEO, CFO, Director, etc."),
    days: int = Query(30),
    is_officer: Optional[bool] = None,
    is_director: Optional[bool] = None,
    exclude_awards: bool = True,
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """
    Screener endpoint — filter Form 4s by role, size, type, date.
    Excludes option awards (txn_code A) by default to show only open-market transactions.
    """
    cutoff = date.today() - timedelta(days=days)
    q = (
        db.query(Form4Filing)
        .filter(
            Form4Filing.txn_date >= cutoff,
            Form4Filing.is_derivative == "N",
            Form4Filing.total_value >= min_value,
        )
    )
    if txn_type:
        q = q.filter(Form4Filing.txn_type == txn_type.upper())
    if max_value:
        q = q.filter(Form4Filing.total_value <= max_value)
    if role:
        q = q.filter(Form4Filing.officer_title.ilike(f"%{role}%"))
    if is_officer is not None:
        q = q.filter(Form4Filing.is_officer == ("1" if is_officer else "0"))
    if is_director is not None:
        q = q.filter(Form4Filing.is_director == ("1" if is_director else "0"))
    if exclude_awards:
        # Exclude grants/awards — focus on open-market buys/sells
        q = q.filter(Form4Filing.txn_code.notin_(["A", "M", "C", "F"]))

    total = q.count()
    items = (
        q.order_by(desc(Form4Filing.total_value))
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return {"total": total, "page": page, "limit": limit, "items": items}
