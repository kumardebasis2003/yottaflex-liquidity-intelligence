
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import text
import json

from app.db import engine
from app.forecast import (
    build_forecast,
    detect_exceptions,
    validate_ground_truth,
)

app = FastAPI(
    title="YottaFlex Liquidity Intelligence",
    description=(
        "Liquidity forecasting, scenario analysis, "
        "exception detection, and ground-truth validation."
    ),
    version="1.0.0",
)

ALLOWED_SCENARIOS = ["BASE", "DELAYED_RECEIPT", "STRESS"]

SUMMARY_TABLES = [
    "legal_entities",
    "bank_accounts",
    "ledger_entries",
    "receivables",
    "payables",
    "currency_rates",
    "cash_flow_forecasts",
    "liquidity_scenarios",
    "forecast_runs",
]


def dataframe_to_records(dataframe):
    """Convert a pandas DataFrame into JSON-safe records."""
    return json.loads(dataframe.to_json(orient="records", date_format="iso"))


@app.get("/")
def home():
    return {
        "application": "YottaFlex Liquidity Intelligence",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "api": "ok",
            "postgresql": "connected",
        }

    except Exception:
        return {
            "api": "ok",
            "postgresql": "error",
        }


@app.get("/api/v1/summary")
def summary():
    """Return record counts for all core database tables."""
    try:
        result = {}

        with engine.connect() as connection:
            for table in SUMMARY_TABLES:
                query = text(f'SELECT COUNT(*) FROM "{table}"')
                result[table] = connection.execute(query).scalar_one()

        result["total_records"] = sum(result.values())
        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve database summary: {str(exc)}",
        )


@app.get("/api/v1/forecast")
def get_forecast(
    scenario: str = Query(
        default="BASE",
        description="BASE, DELAYED_RECEIPT, or STRESS",
    ),
):
    """Return the 30-day liquidity forecast for a selected scenario."""
    scenario = scenario.upper()

    if scenario not in ALLOWED_SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario. Choose one of: {ALLOWED_SCENARIOS}",
        )

    try:
        forecast = build_forecast(scenario=scenario)

        return {
            "scenario": scenario,
            "base_currency": "INR",
            "forecast_days": len(forecast),
            "forecast": dataframe_to_records(forecast),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Forecast generation failed: {str(exc)}",
        )


@app.get("/api/v1/forecast/export.csv")
def export_forecast_csv(
    scenario: str = Query(default="BASE"),
):
    """Download the selected scenario forecast as a CSV file."""
    scenario = scenario.upper()

    if scenario not in ALLOWED_SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario. Choose one of: {ALLOWED_SCENARIOS}",
        )

    try:
        forecast = build_forecast(scenario=scenario)

        return Response(
            content=forecast.to_csv(index=False),
            media_type="text/csv",
            headers={
                "Content-Disposition":
                    f'attachment; filename="liquidity_forecast_{scenario.lower()}.csv"'
            },
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"CSV export failed: {str(exc)}",
        )


@app.get("/api/v1/forecast/export.json")
def export_forecast_json(
    scenario: str = Query(default="BASE"),
):
    """Download the selected scenario forecast as JSON."""
    scenario = scenario.upper()

    if scenario not in ALLOWED_SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario. Choose one of: {ALLOWED_SCENARIOS}",
        )

    try:
        forecast = build_forecast(scenario=scenario)

        return {
            "scenario": scenario,
            "base_currency": "INR",
            "forecast": dataframe_to_records(forecast),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"JSON export failed: {str(exc)}",
        )


@app.get("/api/v1/exceptions")
def get_exceptions():
    """Return detected data-quality and liquidity exceptions."""
    try:
        exceptions = detect_exceptions()

        return {
            "total_exceptions": len(exceptions),
            "exceptions": dataframe_to_records(exceptions),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Exception detection failed: {str(exc)}",
        )


@app.get("/api/v1/exceptions/export.csv")
def export_exceptions_csv():
    """Download detected exceptions as CSV."""
    try:
        exceptions = detect_exceptions()

        return Response(
            content=exceptions.to_csv(index=False),
            media_type="text/csv",
            headers={
                "Content-Disposition":
                    'attachment; filename="liquidity_exceptions.csv"'
            },
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Exception CSV export failed: {str(exc)}",
        )


@app.get("/api/v1/validation")
def get_validation():
    """Compare anomaly detections with the separate ground-truth fixtures."""
    try:
        validation = validate_ground_truth()

        passed = int((validation["result"] == "PASS").sum())
        failed = int((validation["result"] == "FAIL").sum())

        return {
            "status": "PASS" if failed == 0 else "FAIL",
            "total_checks": len(validation),
            "passed": passed,
            "failed": failed,
            "results": dataframe_to_records(validation),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Ground-truth validation failed: {str(exc)}",
        )
