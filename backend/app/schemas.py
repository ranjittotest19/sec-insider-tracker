from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class Form4Row(BaseModel):
    id: int
    accession_number: str
    ticker: Optional[str]
    company_name: Optional[str]
    insider_name: Optional[str]
    officer_title: Optional[str]
    is_director: Optional[str]
    is_officer: Optional[str]
    txn_date: Optional[date]
    shares: Optional[Decimal]
    price_per_share: Optional[Decimal]
    total_value: Optional[Decimal]
    txn_code: Optional[str]
    txn_type: Optional[str]
    shares_owned_after: Optional[Decimal]
    filing_date: Optional[datetime]
    form_url: Optional[str]

    class Config:
        from_attributes = True


class PaginatedForm4(BaseModel):
    total: int
    page: int
    limit: int
    items: List[Form4Row]


class BuySellSummary(BaseModel):
    ticker: str
    buy_count: int
    sell_count: int
    buy_value: float
    sell_value: float
    net_value: float
