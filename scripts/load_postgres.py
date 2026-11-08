
import sys
from pathlib import Path

# Add the project root to Python's import path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sqlalchemy import text
from app.db import engine, Base
from app import models  # Registers all ORM tables

DATA = PROJECT_ROOT / "data" / "generated"


def main():
    if not DATA.exists():
        raise FileNotFoundError(f"Generated data folder not found: {DATA}")

    Base.metadata.create_all(engine)

    order = [
        "legal_entities",
        "bank_accounts",
        "liquidity_scenarios",
        "currency_rates",
        "ledger_entries",
        "receivables",
        "payables",
        "cash_flow_forecasts",
        "forecast_runs",
    ]

    with engine.begin() as conn:
        # Reset only the synthetic demo tables
        for table in reversed(order):
            conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))

        for table in order:
            path = DATA / f"{table}.csv"

            if not path.exists():
                raise FileNotFoundError(f"CSV file not found: {path}")

            df = pd.read_csv(path)

            df.to_sql(
                table,
                conn,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=1000,
            )

            print(f"Loaded {len(df):,} rows into {table}")

    print("\nPostgreSQL load complete!")


if __name__ == "__main__":
    main()
