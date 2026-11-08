# YottaFlex Liquidity Intelligence Platform

A synthetic-data MVP for consolidating legal entities, bank accounts, ledger activity and expected cash flows; forecasting short-term liquidity under base, delayed-receipt and stress scenarios; and detecting selected data-quality exceptions.

## Requirements
- Python 3.10+
- PostgreSQL 14+
- Windows PowerShell (commands below)

## Setup
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```
Edit `.env` and set your PostgreSQL password. Create the database:
```sql
CREATE DATABASE yottaflex_liquidity;
```

## Generate synthetic data
Starter:
```powershell
python scripts/generate_data.py --scale small --seed 20261022
```
Full assignment volume:
```powershell
python scripts/generate_data.py --scale full --seed 20261022
```
Ground truth labels are exported separately to `data/ground_truth/ground_truth.csv`.

## Load PostgreSQL
```powershell
python scripts/load_postgres.py
```
The loader truncates the synthetic demo tables before loading. Do not use it against production data.

## Run API
```powershell
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs

## Run dashboard
In another PowerShell window:
```powershell
.venv\Scripts\Activate.ps1
streamlit run dashboard.py
```

## Tests
```powershell
pytest -q
```

## Important assumptions and limitations
- All records are synthetic and generated with NumPy seed 20261022.
- INR conversion in the MVP uses documented illustrative fallback rates in `app/forecast.py`; the generated daily FX-rate table is included for later date-specific rate integration.
- The MVP calculates 30-day scenarios and detects balance mismatches and duplicate forecast records. Missing FX, actual-after-cutoff and mixed-currency cases are documented as ground-truth test fixtures; they should be expanded into executable exception tests before production use.
- This is a demonstration, not a banking or treasury production system.
