import argparse
from pathlib import Path
import numpy as np
import pandas as pd

OUT = Path("data/generated")
GT = Path("data/ground_truth")
SEED_DEFAULT = 20261022
AS_OF = pd.Timestamp("2026-11-08")
CURRENCIES = ["INR", "USD", "EUR", "GBP", "SGD"]
FX_TO_INR = {"INR": 1.0, "USD": 83.0, "EUR": 90.0, "GBP": 105.0, "SGD": 62.0}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", choices=["small", "full"], default="small")
    parser.add_argument("--seed", type=int, default=SEED_DEFAULT)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)
    OUT.mkdir(parents=True, exist_ok=True)
    GT.mkdir(parents=True, exist_ok=True)

    n_entities = 30 if args.scale == "full" else 5
    n_accounts = 150 if args.scale == "full" else 15
    n_ledger = 100_000 if args.scale == "full" else 1_000
    n_forecasts = 20_000 if args.scale == "full" else 300

    entities = []
    for i in range(1, n_entities + 1):
        entities.append({
            "entity_id": f"ENT-{i:06d}", "entity_name": f"Demo Legal Entity {i:02d}",
            "country": "India", "base_currency": "INR", "status": "ACTIVE"
        })
    entity_df = pd.DataFrame(entities)

    accounts = []
    for i in range(1, n_accounts + 1):
        entity_num = ((i - 1) % n_entities) + 1
        currency = CURRENCIES[(i - 1) % len(CURRENCIES)]
        opening = round(float(rng.uniform(500_000, 8_000_000)), 2)
        accounts.append({
            "account_id": f"BANKACC-ENT-{entity_num:06d}-{((i-1)//n_entities)+1:03d}",
            "entity_id": f"ENT-{entity_num:06d}", "bank_name": ["Demo Bank A","Demo Bank B","Demo Bank C"][i % 3],
            "currency": currency, "opening_balance": opening, "closing_balance": opening,
            "effective_date": AS_OF.date(), "status": "ACTIVE"
        })
    account_df = pd.DataFrame(accounts)
    account_ids = account_df["account_id"].to_numpy()
    account_currency = account_df.set_index("account_id")["currency"].to_dict()
    account_entity = account_df.set_index("account_id")["entity_id"].to_dict()

    ledger = []
    net_by_account = {a: 0.0 for a in account_ids}
    start = AS_OF - pd.Timedelta(days=30)
    for i in range(1, n_ledger + 1):
        aid = str(rng.choice(account_ids))
        amount_abs = round(float(rng.uniform(100, 50_000)), 2)
        direction = "CREDIT" if rng.random() < 0.52 else "DEBIT"
        amount = amount_abs if direction == "CREDIT" else -amount_abs
        net_by_account[aid] += amount
        dt = start + pd.Timedelta(days=int(rng.integers(0, 30)))
        ledger.append({
            "ledger_id": f"LED-2026-{i:08d}", "account_id": aid,
            "transaction_date": dt.date(), "transaction_type": direction,
            "amount": amount, "currency": account_currency[aid],
            "description": f"Synthetic {direction.lower()} transaction"
        })
    ledger_df = pd.DataFrame(ledger)
    account_df["closing_balance"] = account_df.apply(
        lambda r: round(float(r["opening_balance"]) + net_by_account[r["account_id"]], 2), axis=1
    )

    receivables, payables, forecast = [], [], []
    for i in range(1, n_forecasts + 1):
        aid = str(rng.choice(account_ids))
        eid = account_entity[aid]
        dt = AS_OF + pd.Timedelta(days=int(rng.integers(1, 31)))
        amt = round(float(rng.uniform(5_000, 500_000)), 2)
        cur = account_currency[aid]
        if i % 2:
            rid = f"REC-{i:06d}"
            receivables.append({
                "receivable_id": rid, "entity_id": eid, "account_id": aid,
                "expected_date": dt.date(), "actual_date": None, "amount": amt,
                "currency": cur, "status": "SCHEDULED"
            })
            direction, source_type, source_id = "INFLOW", "RECEIVABLE", rid
        else:
            rid = f"PAY-{i:06d}"
            payables.append({
                "payable_id": rid, "entity_id": eid, "account_id": aid,
                "expected_date": dt.date(), "actual_date": None, "amount": amt,
                "currency": cur, "status": "SCHEDULED"
            })
            direction, source_type, source_id = "OUTFLOW", "PAYABLE", rid
        forecast.append({
            "forecast_id": f"CF-2026-{i:06d}", "entity_id": eid, "account_id": aid,
            "source_type": source_type, "source_id": source_id,
            "forecast_date": dt.date(), "amount": amt, "currency": cur,
            "direction": direction, "cutoff_date": AS_OF.date()
        })

    receivable_df = pd.DataFrame(receivables)
    payable_df = pd.DataFrame(payables)
    forecast_df = pd.DataFrame(forecast)

    rate_rows = []
    for day in pd.date_range(AS_OF - pd.Timedelta(days=30), AS_OF + pd.Timedelta(days=30)):
        for cur in CURRENCIES:
            base = FX_TO_INR[cur]
            rate_rows.append({
                "rate_id": f"FX-{cur}-INR-{day:%Y%m%d}", "from_currency": cur,
                "to_currency": "INR", "rate_date": day.date(),
                "exchange_rate": round(base * float(rng.uniform(0.985, 1.015)), 6)
            })
    rates_df = pd.DataFrame(rate_rows)

    scenarios_df = pd.DataFrame([
        {"scenario_id":"SCN-001","scenario_name":"BASE","receipt_delay_days":0,"payment_multiplier":1.0,"description":"Expected dates and expected payments."},
        {"scenario_id":"SCN-002","scenario_name":"DELAYED_RECEIPT","receipt_delay_days":7,"payment_multiplier":1.0,"description":"Receipts delayed by seven days."},
        {"scenario_id":"SCN-003","scenario_name":"STRESS","receipt_delay_days":14,"payment_multiplier":1.15,"description":"Receipts delayed fourteen days and payments increased by 15 percent."}
    ])
    runs_df = pd.DataFrame([
        {"run_id":f"FCAST-2026-11-08-{i:03d}","scenario_id":f"SCN-{i:03d}",
         "run_date":AS_OF.date(),"cutoff_date":AS_OF.date(),"version":1,"status":"COMPLETED"}
        for i in range(1,4)
    ])

    # Five deliberately labelled test cases. These labels are NOT included in model input tables.
    ground_truth = pd.DataFrame([
        {"issue_id":"GT-001","issue_type":"BALANCE_MISMATCH","record_id":str(account_df.iloc[0]["account_id"]),"expected_detection":True,"description":"Test case: closing balance altered in isolated anomaly fixture."},
        {"issue_id":"GT-002","issue_type":"MISSING_FX_RATE","record_id":"FX-TEST-USD-001","expected_detection":True,"description":"Test case: foreign currency has no matching FX rate."},
        {"issue_id":"GT-003","issue_type":"DUPLICATE_CASH_FLOW","record_id":str(forecast_df.iloc[0]["forecast_id"]),"expected_detection":True,"description":"Test case: duplicate forecast fixture."},
        {"issue_id":"GT-004","issue_type":"ACTUAL_AFTER_CUTOFF","record_id":"ACTUAL-TEST-001","expected_detection":True,"description":"Test case: actual event timestamp is after forecast cutoff."},
        {"issue_id":"GT-005","issue_type":"MIXED_CURRENCY","record_id":"MIXED-CURRENCY-TEST-001","expected_detection":True,"description":"Test case: mixed currency aggregation without conversion."}
    ])

    datasets = {
        "legal_entities": entity_df, "bank_accounts": account_df, "ledger_entries": ledger_df,
        "receivables": receivable_df, "payables": payable_df, "cash_flow_forecasts": forecast_df,
        "currency_rates": rates_df, "liquidity_scenarios": scenarios_df, "forecast_runs": runs_df
    }
    for name, df in datasets.items():
        df.to_csv(OUT / f"{name}.csv", index=False)
    ground_truth.to_csv(GT / "ground_truth.csv", index=False)

    manifest = pd.DataFrame([{"dataset":k,"rows":len(v),"seed":args.seed,"scale":args.scale} for k,v in datasets.items()])
    manifest.to_csv(OUT / "manifest.csv", index=False)
    print(manifest.to_string(index=False))
    print(f"\nGenerated data with seed={args.seed}, scale={args.scale}")
    print(f"Ground truth saved separately: {GT / 'ground_truth.csv'}")

if __name__ == "__main__":
    main()
