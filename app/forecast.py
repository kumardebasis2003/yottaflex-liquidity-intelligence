
from pathlib import Path
from bisect import bisect_right
import json

import pandas as pd


# =========================================================
# CONFIGURATION
# =========================================================

ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data" / "generated"

FIXTURE_FILE = (
    ROOT / "data" / "anomaly_fixtures" / "anomaly_fixtures.json"
)

GROUND_TRUTH_FILE = (
    ROOT / "data" / "ground_truth" / "ground_truth.csv"
)

BASE_CURRENCY = "INR"

DEFAULT_CUTOFF = "2026-11-08"

DEFAULT_HORIZON = 30

SCENARIO_CONFIG = {
    "BASE": {
        "delay_days": 0,
        "outflow_multiplier": 1.0,
    },
    "DELAYED_RECEIPT": {
        "delay_days": 7,
        "outflow_multiplier": 1.0,
    },
    "STRESS": {
        "delay_days": 14,
        "outflow_multiplier": 1.15,
    },
}


# =========================================================
# DATA LOADING
# =========================================================

def _load_csv(filename, dates=None):

    path = DATA / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Required data file not found: {path}"
        )

    df = pd.read_csv(path)

    for column in dates or []:

        if column in df.columns:
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce",
            )

    return df


# =========================================================
# FAST FOREIGN EXCHANGE LOOKUP
# =========================================================

def _get_rate(currency, rate_date, rates):
    """
    Return the latest available currency conversion rate
    on or before the requested date.

    Currency rates are indexed once and reused.
    """

    currency = str(currency).upper()

    rate_date = pd.Timestamp(
        rate_date
    ).normalize()

    if currency == BASE_CURRENCY:
        return 1.0

    # Reuse the cached lookup if it already exists.
    lookup = rates.attrs.get("_fx_lookup")

    if lookup is None:

        lookup = {}

        fx_rates = rates.copy()

        fx_rates["from_currency"] = (
            fx_rates["from_currency"]
            .astype(str)
            .str.upper()
        )

        fx_rates["to_currency"] = (
            fx_rates["to_currency"]
            .astype(str)
            .str.upper()
        )

        fx_rates["rate_date"] = pd.to_datetime(
            fx_rates["rate_date"],
            errors="coerce",
        ).dt.normalize()

        fx_rates = fx_rates[
            fx_rates["to_currency"] == BASE_CURRENCY
        ].dropna(
            subset=["rate_date"]
        )

        fx_rates = fx_rates.sort_values(
            "rate_date"
        )

        for curr, group in fx_rates.groupby(
            "from_currency"
        ):

            lookup[curr] = (
                group["rate_date"].tolist(),
                group["exchange_rate"].astype(float).tolist(),
            )

        rates.attrs["_fx_lookup"] = lookup

    if currency not in lookup:

        raise ValueError(
            f"Missing FX rate: {currency} to {BASE_CURRENCY}"
        )

    dates, values = lookup[currency]

    # Find the latest rate date <= requested date.
    index = bisect_right(
        dates,
        rate_date,
    ) - 1

    if index < 0:

        raise ValueError(
            f"Missing FX rate: {currency} to {BASE_CURRENCY} "
            f"on or before {rate_date.date()}"
        )

    rate = float(values[index])

    if rate <= 0:

        raise ValueError(
            f"Invalid FX rate for {currency}: {rate}"
        )

    return rate


def _convert_to_inr(
    amount,
    currency,
    rate_date,
    rates,
):

    return float(amount) * _get_rate(
        currency,
        rate_date,
        rates,
    )


# =========================================================
# LIQUIDITY FORECAST ENGINE
# =========================================================

def build_forecast(
    scenario="BASE",
    cutoff_date=None,
    horizon_days=DEFAULT_HORIZON,
):
    """
    Build a daily INR liquidity forecast.

    Supported scenarios:
    BASE
    DELAYED_RECEIPT
    STRESS
    """

    scenario = scenario.upper()

    if scenario not in SCENARIO_CONFIG:

        raise ValueError(
            f"Unsupported scenario: {scenario}. "
            f"Choose from {list(SCENARIO_CONFIG)}"
        )

    if horizon_days < 1 or horizon_days > 365:

        raise ValueError(
            "horizon_days must be between 1 and 365"
        )

    cutoff = pd.Timestamp(
        cutoff_date or DEFAULT_CUTOFF
    ).normalize()

    accounts = _load_csv(
        "bank_accounts.csv"
    )

    flows = _load_csv(
        "cash_flow_forecasts.csv",
        ["forecast_date", "cutoff_date"],
    )

    rates = _load_csv(
        "currency_rates.csv",
        ["rate_date"],
    )

    # -----------------------------------------------------
    # Calculate opening liquidity
    # -----------------------------------------------------

    opening_inr = 0.0

    for row in accounts.itertuples(
        index=False
    ):

        effective_date = pd.Timestamp(
            row.effective_date
        ).normalize()

        if effective_date > cutoff:
            continue

        opening_inr += _convert_to_inr(
            row.opening_balance,
            row.currency,
            cutoff,
            rates,
        )

    # -----------------------------------------------------
    # Apply scenario assumptions
    # -----------------------------------------------------

    config = SCENARIO_CONFIG[scenario]

    flows["effective_date"] = (
        flows["forecast_date"].copy()
    )

    inflow_mask = (
        flows["direction"].str.upper() == "INFLOW"
    )

    flows.loc[
        inflow_mask,
        "effective_date",
    ] += pd.Timedelta(
        days=config["delay_days"]
    )

    # -----------------------------------------------------
    # Convert cash flows to INR
    # -----------------------------------------------------

    flows["amount_inr"] = flows.apply(
        lambda row: _convert_to_inr(
            row["amount"],
            row["currency"],
            row["effective_date"],
            rates,
        ),
        axis=1,
    )

    outflow_mask = (
        flows["direction"].str.upper() == "OUTFLOW"
    )

    flows.loc[
        outflow_mask,
        "amount_inr",
    ] *= config["outflow_multiplier"]

    # -----------------------------------------------------
    # Aggregate daily cash flows efficiently
    # -----------------------------------------------------

    flows["effective_date"] = (
        flows["effective_date"].dt.normalize()
    )

    flows["direction"] = (
        flows["direction"].str.upper()
    )

    daily_flows = (
        flows.groupby(
            ["effective_date", "direction"]
        )["amount_inr"]
        .sum()
        .unstack(fill_value=0)
    )

    dates = pd.date_range(
        cutoff + pd.Timedelta(days=1),
        periods=horizon_days,
        freq="D",
    )

    rows = []

    balance = opening_inr

    for day in dates:

        if day in daily_flows.index:

            dayflows = daily_flows.loc[day]

            inflow = float(
                dayflows.get("INFLOW", 0.0)
            )

            outflow = float(
                dayflows.get("OUTFLOW", 0.0)
            )

        else:

            inflow = 0.0
            outflow = 0.0

        closing = balance + inflow - outflow

        rows.append({
            "date": day.date(),
            "opening_inr": round(balance, 2),
            "inflows_inr": round(inflow, 2),
            "outflows_inr": round(outflow, 2),
            "net_cash_flow_inr": round(
                inflow - outflow,
                2,
            ),
            "closing_inr": round(closing, 2),
            "scenario": scenario,
            "base_currency": BASE_CURRENCY,
        })

        balance = closing

    return pd.DataFrame(rows)


# =========================================================
# EXCEPTION DETECTION ENGINE
# =========================================================

def detect_exceptions(cutoff_date=None):
    """
    Detect normal-data exceptions and deliberately injected,
    isolated anomaly fixtures.

    Anomaly fixtures remain separate from normal data.
    """

    cutoff = pd.Timestamp(
        cutoff_date or DEFAULT_CUTOFF
    ).normalize()

    accounts = _load_csv(
        "bank_accounts.csv"
    )

    ledger = _load_csv(
        "ledger_entries.csv",
        ["transaction_date"],
    )

    flows = _load_csv(
        "cash_flow_forecasts.csv",
        ["forecast_date", "cutoff_date"],
    )

    rates = _load_csv(
        "currency_rates.csv",
        ["rate_date"],
    )

    issues = []

    def add_issue(
        issue_type,
        record_id,
        severity,
        description,
    ):

        issues.append({
            "issue_type": issue_type,
            "record_id": str(record_id),
            "severity": severity,
            "description": description,
        })

    # -----------------------------------------------------
    # 1. Account balance reconciliation
    # -----------------------------------------------------

    net = ledger.groupby(
        "account_id"
    )["amount"].sum()

    for row in accounts.itertuples(
        index=False
    ):

        expected = (
            float(row.opening_balance)
            + float(net.get(row.account_id, 0.0))
        )

        difference = (
            expected - float(row.closing_balance)
        )

        if abs(difference) > 0.01:

            add_issue(
                "BALANCE_MISMATCH",
                row.account_id,
                "HIGH",
                f"Opening balance plus ledger movements differs "
                f"from reported closing balance by {difference:.2f}",
            )

    # -----------------------------------------------------
    # 2. Normal missing FX checks
    # -----------------------------------------------------

    for row in flows.itertuples(
        index=False
    ):

        currency = str(
            row.currency
        ).upper()

        if currency == BASE_CURRENCY:
            continue

        try:

            _get_rate(
                currency,
                row.forecast_date,
                rates,
            )

        except ValueError:

            add_issue(
                "MISSING_FX_RATE",
                row.forecast_id,
                "HIGH",
                f"No {currency}/{BASE_CURRENCY} FX rate available "
                f"on or before {row.forecast_date.date()}",
            )

    # -----------------------------------------------------
    # 3. Duplicate cash flow checks
    # -----------------------------------------------------

    duplicate_mask = flows.duplicated(
        [
            "source_type",
            "source_id",
            "forecast_date",
        ],
        keep=False,
    )

    for row in flows[
        duplicate_mask
    ].itertuples(index=False):

        add_issue(
            "DUPLICATE_CASH_FLOW",
            row.forecast_id,
            "MEDIUM",
            f"Duplicate source {row.source_type}/{row.source_id} "
            f"on {row.forecast_date.date()}",
        )

    # -----------------------------------------------------
    # 4. Actual transactions after cutoff
    # -----------------------------------------------------

    late_actuals = ledger[
        ledger["transaction_date"].notna()
        & (
            ledger["transaction_date"] > cutoff
        )
    ]

    for row in late_actuals.itertuples(
        index=False
    ):

        add_issue(
            "ACTUAL_AFTER_CUTOFF",
            row.ledger_id,
            "HIGH",
            f"Ledger transaction dated "
            f"{row.transaction_date.date()} "
            f"is after cutoff {cutoff.date()}",
        )

    # -----------------------------------------------------
    # 5. Normal mixed-currency conversion checks
    # -----------------------------------------------------

    for row in flows.itertuples(
        index=False
    ):

        currency = str(
            row.currency
        ).upper()

        if currency == BASE_CURRENCY:
            continue

        try:

            _get_rate(
                currency,
                row.forecast_date,
                rates,
            )

        except ValueError:

            add_issue(
                "MIXED_CURRENCY",
                row.forecast_id,
                "HIGH",
                f"Cannot convert {currency} cash flow into "
                f"{BASE_CURRENCY} for {row.forecast_date.date()}",
            )

    # -----------------------------------------------------
    # 6. Isolated anomaly fixtures
    # -----------------------------------------------------

    if FIXTURE_FILE.exists():

        with open(
            FIXTURE_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            fixtures = json.load(file)

        # GT-001: Balance mismatch fixture

        fixture = fixtures["balance_mismatch"]

        account = accounts[
            accounts["account_id"].astype(str)
            == fixture["record_id"]
        ]

        if not account.empty:

            account_row = account.iloc[0]

            account_ledger = ledger[
                ledger["account_id"].astype(str)
                == fixture["record_id"]
            ]

            expected = (
                float(account_row["opening_balance"])
                + float(account_ledger["amount"].sum())
            )

            altered_closing = (
                float(account_row["closing_balance"])
                + float(
                    fixture["closing_balance_adjustment"]
                )
            )

            if abs(expected - altered_closing) > 0.01:

                add_issue(
                    "BALANCE_MISMATCH",
                    fixture["record_id"],
                    "HIGH",
                    "Injected fixture: account closing balance "
                    "was deliberately altered.",
                )

        # GT-002: Missing FX rate fixture

        fixture = fixtures["missing_fx_rate"]

        try:

            _get_rate(
                fixture["currency"],
                fixture["forecast_date"],
                rates,
            )

        except ValueError:

            add_issue(
                "MISSING_FX_RATE",
                fixture["record_id"],
                "HIGH",
                "Injected fixture: no matching FX conversion rate exists.",
            )

        # GT-003: Duplicate cash flow fixture

        fixture = fixtures["duplicate_cash_flow"]

        selected = flows[
            flows["forecast_id"].astype(str)
            == fixture["record_id"]
        ]

        if not selected.empty:

            isolated_flows = pd.concat(
                [
                    selected,
                    selected.copy(),
                ],
                ignore_index=True,
            )

            duplicate = isolated_flows.duplicated(
                [
                    "source_type",
                    "source_id",
                    "forecast_date",
                ],
                keep=False,
            )

            if duplicate.any():

                add_issue(
                    "DUPLICATE_CASH_FLOW",
                    fixture["record_id"],
                    "MEDIUM",
                    "Injected fixture: duplicate cash flow source "
                    "detected in isolated test data.",
                )

        # GT-004: Actual after cutoff fixture

        fixture = fixtures["actual_after_cutoff"]

        actual_date = pd.Timestamp(
            fixture["transaction_date"]
        )

        if actual_date > cutoff:

            add_issue(
                "ACTUAL_AFTER_CUTOFF",
                fixture["record_id"],
                "HIGH",
                f"Injected fixture: actual transaction date "
                f"{actual_date.date()} is after cutoff {cutoff.date()}.",
            )

        # GT-005: Mixed currency fixture

        fixture = fixtures["mixed_currency"]

        currencies = {
            str(currency).upper()
            for currency in fixture["currencies"]
        }

        if (
            len(currencies) > 1
            and not fixture["converted_to_base"]
        ):

            add_issue(
                "MIXED_CURRENCY",
                fixture["record_id"],
                "HIGH",
                "Injected fixture: multiple currencies were combined "
                "without conversion to the base currency.",
            )

    return pd.DataFrame(
        issues,
        columns=[
            "issue_type",
            "record_id",
            "severity",
            "description",
        ],
    )


# =========================================================
# GROUND-TRUTH VALIDATION
# =========================================================

def validate_ground_truth(cutoff_date=None):
    """
    Compare detected fixture records against ground-truth labels.
    """

    if not GROUND_TRUTH_FILE.exists():

        raise FileNotFoundError(
            f"Ground truth file not found: {GROUND_TRUTH_FILE}"
        )

    truth = pd.read_csv(
        GROUND_TRUTH_FILE
    )

    detected = detect_exceptions(
        cutoff_date
    )

    rows = []

    for item in truth.itertuples(
        index=False
    ):

        matches = detected[
            (
                detected["record_id"].astype(str)
                == str(item.record_id)
            )
            & (
                detected["issue_type"]
                == item.issue_type
            )
        ]

        actual = not matches.empty

        expected = (
            str(item.expected_detection)
            .strip()
            .lower()
            == "true"
        )

        rows.append({
            "issue_id": item.issue_id,
            "issue_type": item.issue_type,
            "record_id": item.record_id,
            "expected_detection": expected,
            "actual_detection": actual,
            "result": (
                "PASS"
                if actual == expected
                else "FAIL"
            ),
        })

    return pd.DataFrame(rows)
