
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "generated"
FIXTURES = ROOT / "data" / "anomaly_fixtures"
GROUND_TRUTH = ROOT / "data" / "ground_truth" / "ground_truth.csv"

CUTOFF = pd.Timestamp("2026-11-08")

def main():
    FIXTURES.mkdir(parents=True, exist_ok=True)

    accounts = pd.read_csv(DATA / "bank_accounts.csv")
    flows = pd.read_csv(DATA / "cash_flow_forecasts.csv")

    account_id = str(accounts.iloc[0]["account_id"])
    forecast_id = str(flows.iloc[0]["forecast_id"])

    fixtures = {
        "cutoff_date": str(CUTOFF.date()),
        "balance_mismatch": {
            "record_id": account_id,
            "closing_balance_adjustment": 1000.0
        },
        "missing_fx_rate": {
            "record_id": "FX-TEST-USD-001",
            "currency": "USD",
            "forecast_date": "1900-01-01",
            "amount": 1000.0
        },
        "duplicate_cash_flow": {
            "record_id": forecast_id
        },
        "actual_after_cutoff": {
            "record_id": "ACTUAL-TEST-001",
            "transaction_date": "2026-11-09",
            "amount": -500.0,
            "currency": "INR"
        },
        "mixed_currency": {
            "record_id": "MIXED-CURRENCY-TEST-001",
            "aggregation_id": "MIXED-001",
            "currencies": ["INR", "USD"],
            "converted_to_base": False,
            "amounts": [1000.0, 100.0]
        }
    }

    with open(FIXTURES / "anomaly_fixtures.json", "w", encoding="utf-8") as f:
        json.dump(fixtures, f, indent=4)

    print("Anomaly fixtures generated successfully.")
    print(f"Location: {FIXTURES / 'anomaly_fixtures.json'}")
    print("Five isolated anomaly fixtures created.")

if __name__ == "__main__":
    main()
