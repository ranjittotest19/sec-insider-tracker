from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Text, Index
from sqlalchemy.sql import func
from app.database import Base


class Form4Filing(Base):
    __tablename__ = "form4_filings"

    id = Column(Integer, primary_key=True, index=True)
    accession_number = Column(String(25), unique=True, nullable=False)

    # Issuer (company)
    issuer_cik = Column(String(10), nullable=False)
    ticker = Column(String(10), index=True)
    company_name = Column(String(255))

    # Reporting owner (insider)
    insider_cik = Column(String(10), nullable=False)
    insider_name = Column(String(255), index=True)
    is_director = Column(String(1))
    is_officer = Column(String(1))
    is_ten_pct_owner = Column(String(1))
    officer_title = Column(String(255))

    # Transaction
    txn_date = Column(Date, index=True)
    shares = Column(Numeric(20, 4))
    price_per_share = Column(Numeric(20, 4))
    total_value = Column(Numeric(20, 2), index=True)
    txn_code = Column(String(2))          # P=Purchase, S=Sale, A=Award, etc.
    txn_type = Column(String(1), index=True)   # A=Acquired, D=Disposed
    is_direct = Column(String(1))         # D=Direct, I=Indirect
    shares_owned_after = Column(Numeric(20, 4))

    # Is it a derivative transaction?
    is_derivative = Column(String(1), default="N")
    security_title = Column(String(255))

    # Meta
    filing_date = Column(DateTime, index=True)
    form_url = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_form4_ticker_date", "ticker", "txn_date"),
        Index("ix_form4_insider_date", "insider_cik", "txn_date"),
        Index("ix_form4_filing_date", "filing_date"),
        Index("ix_form4_txn_type_date", "txn_type", "txn_date"),
    )


class Filing13DG(Base):
    __tablename__ = "filings_13dg"

    id = Column(Integer, primary_key=True, index=True)
    accession_number = Column(String(25), unique=True, nullable=False)

    form_type = Column(String(10), index=True)  # SC 13D, SC 13G, SC 13D/A, SC 13G/A

    # Subject company
    subject_cik = Column(String(10))
    subject_ticker = Column(String(10), index=True)
    subject_company = Column(String(255))

    # Filer
    filer_cik = Column(String(10), nullable=False)
    filer_name = Column(String(255), index=True)

    # Holdings
    percent_owned = Column(Numeric(6, 3))
    shares_owned = Column(Numeric(20, 0))
    event_date = Column(Date, index=True)

    # Meta
    filing_date = Column(DateTime, index=True)
    form_url = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_13dg_ticker_date", "subject_ticker", "filing_date"),
        Index("ix_13dg_filer_date", "filer_cik", "filing_date"),
    )


class CompanyInfo(Base):
    """Cache of CIK → ticker/company mappings from SEC"""
    __tablename__ = "company_info"

    id = Column(Integer, primary_key=True, index=True)
    cik = Column(String(10), unique=True, nullable=False, index=True)
    ticker = Column(String(10), index=True)
    company_name = Column(String(255))
    sic = Column(String(4))
    state_inc = Column(String(2))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
