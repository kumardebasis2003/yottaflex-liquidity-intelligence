from sqlalchemy import Column, String, Integer, Date, DateTime, Numeric, ForeignKey, Boolean, Text, UniqueConstraint
from sqlalchemy.sql import func
from app.db import Base

class LegalEntity(Base):
    __tablename__ = "legal_entities"
    entity_id = Column(String, primary_key=True)
    entity_name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    base_currency = Column(String, nullable=False)
    status = Column(String, nullable=False)

class BankAccount(Base):
    __tablename__ = "bank_accounts"
    account_id = Column(String, primary_key=True)
    entity_id = Column(String, ForeignKey("legal_entities.entity_id"), nullable=False)
    bank_name = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    opening_balance = Column(Numeric(18,2), nullable=False)
    closing_balance = Column(Numeric(18,2), nullable=False)
    effective_date = Column(Date, nullable=False)
    status = Column(String, nullable=False)

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    ledger_id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("bank_accounts.account_id"), nullable=False)
    transaction_date = Column(Date, nullable=False)
    transaction_type = Column(String, nullable=False)
    amount = Column(Numeric(18,2), nullable=False)
    currency = Column(String, nullable=False)
    description = Column(String, nullable=False)

class Receivable(Base):
    __tablename__ = "receivables"
    receivable_id = Column(String, primary_key=True)
    entity_id = Column(String, ForeignKey("legal_entities.entity_id"), nullable=False)
    account_id = Column(String, ForeignKey("bank_accounts.account_id"), nullable=False)
    expected_date = Column(Date, nullable=False)
    actual_date = Column(Date, nullable=True)
    amount = Column(Numeric(18,2), nullable=False)
    currency = Column(String, nullable=False)
    status = Column(String, nullable=False)

class Payable(Base):
    __tablename__ = "payables"
    payable_id = Column(String, primary_key=True)
    entity_id = Column(String, ForeignKey("legal_entities.entity_id"), nullable=False)
    account_id = Column(String, ForeignKey("bank_accounts.account_id"), nullable=False)
    expected_date = Column(Date, nullable=False)
    actual_date = Column(Date, nullable=True)
    amount = Column(Numeric(18,2), nullable=False)
    currency = Column(String, nullable=False)
    status = Column(String, nullable=False)

class CurrencyRate(Base):
    __tablename__ = "currency_rates"
    rate_id = Column(String, primary_key=True)
    from_currency = Column(String, nullable=False)
    to_currency = Column(String, nullable=False)
    rate_date = Column(Date, nullable=False)
    exchange_rate = Column(Numeric(18,6), nullable=False)
    __table_args__ = (UniqueConstraint("from_currency", "to_currency", "rate_date"),)

class CashFlowForecast(Base):
    __tablename__ = "cash_flow_forecasts"
    forecast_id = Column(String, primary_key=True)
    entity_id = Column(String, ForeignKey("legal_entities.entity_id"), nullable=False)
    account_id = Column(String, ForeignKey("bank_accounts.account_id"), nullable=False)
    source_type = Column(String, nullable=False)
    source_id = Column(String, nullable=False)
    forecast_date = Column(Date, nullable=False)
    amount = Column(Numeric(18,2), nullable=False)
    currency = Column(String, nullable=False)
    direction = Column(String, nullable=False)
    cutoff_date = Column(Date, nullable=False)

class LiquidityScenario(Base):
    __tablename__ = "liquidity_scenarios"
    scenario_id = Column(String, primary_key=True)
    scenario_name = Column(String, nullable=False, unique=True)
    receipt_delay_days = Column(Integer, nullable=False)
    payment_multiplier = Column(Numeric(8,3), nullable=False)
    description = Column(Text, nullable=False)

class ForecastRun(Base):
    __tablename__ = "forecast_runs"
    run_id = Column(String, primary_key=True)
    scenario_id = Column(String, ForeignKey("liquidity_scenarios.scenario_id"), nullable=False)
    run_date = Column(Date, nullable=False)
    cutoff_date = Column(Date, nullable=False)
    version = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DailyCashPosition(Base):
    __tablename__ = "daily_cash_positions"
    position_id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("forecast_runs.run_id"), nullable=False)
    position_date = Column(Date, nullable=False)
    opening_balance_inr = Column(Numeric(20,2), nullable=False)
    inflows_inr = Column(Numeric(20,2), nullable=False)
    outflows_inr = Column(Numeric(20,2), nullable=False)
    closing_balance_inr = Column(Numeric(20,2), nullable=False)

class ExceptionRecord(Base):
    __tablename__ = "exception_records"
    issue_id = Column(String, primary_key=True)
    issue_type = Column(String, nullable=False)
    record_id = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    status = Column(String, nullable=False)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())

class AuditEvent(Base):
    __tablename__ = "audit_events"
    event_id = Column(String, primary_key=True)
    entity_type = Column(String, nullable=False)
    record_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    event_details = Column(Text, nullable=False)
    event_timestamp = Column(DateTime(timezone=True), server_default=func.now())
