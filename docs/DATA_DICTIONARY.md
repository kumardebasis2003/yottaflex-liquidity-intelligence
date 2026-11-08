# Data Dictionary (MVP)

| Entity | Primary key | Main fields | Relationship |
|---|---|---|---|
| LegalEntity | entity_id | entity_name, country, base_currency, status | 1:N BankAccount, Receivable, Payable |
| BankAccount | account_id | entity_id, currency, opening_balance, closing_balance | N:1 LegalEntity; 1:N LedgerEntry |
| LedgerEntry | ledger_id | account_id, transaction_date, amount, currency | N:1 BankAccount |
| CashFlowForecast | forecast_id | entity_id, account_id, source_type, source_id, forecast_date, amount, direction | N:1 LegalEntity and BankAccount |
| Receivable | receivable_id | entity_id, account_id, expected_date, actual_date, amount, status | N:1 LegalEntity and BankAccount |
| Payable | payable_id | entity_id, account_id, expected_date, actual_date, amount, status | N:1 LegalEntity and BankAccount |
| CurrencyRate | rate_id | from_currency, to_currency, rate_date, exchange_rate | Unique currency pair/date |
| LiquidityScenario | scenario_id | scenario_name, receipt_delay_days, payment_multiplier | 1:N ForecastRun |
| ForecastRun | run_id | scenario_id, run_date, cutoff_date, version, status | N:1 LiquidityScenario |

Money is stored in decimal/numeric columns in PostgreSQL. Synthetic CSV generation uses decimal-rounded values. Currency codes: INR, USD, EUR, GBP, SGD. IDs are immutable strings with zero-padded counters.
