
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.forecast import (
    build_forecast,
    detect_exceptions,
    validate_ground_truth,
)

# =========================================================
# CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="YottaFlex | Treasury Intelligence",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data" / "generated"

NAVY = "#101D35"
BLUE = "#3867F5"
TEAL = "#13B8A6"
MUTED = "#718096"
BG = "#F4F7FB"

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #F4F7FB;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}

[data-testid="stSidebar"] {
    background: #101D35;
    border-right: none;
}

[data-testid="stSidebar"] * {
    color: #E8EEF8 !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #AAB8CC !important;
}

[data-testid="stSidebar"] .stRadio label {
    padding: 8px 10px;
    border-radius: 8px;
}

[data-testid="stSidebar"] hr {
    border-color: #34435B;
}

.brand {
    font-size: 25px;
    font-weight: 800;
    color: white;
    letter-spacing: -1px;
    padding: 10px 0 3px 0;
}

.brand span {
    color: #5F91FF;
}

.brand-sub {
    color: #9CAEC7;
    font-size: 11px;
    letter-spacing: 1.5px;
    margin-bottom: 30px;
}

.top-label {
    color: #718096;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1.4px;
    text-transform: uppercase;
}

.page-title {
    font-size: 30px;
    font-weight: 800;
    color: #15233B;
    letter-spacing: -1px;
    margin: 5px 0 2px 0;
}

.page-subtitle {
    color: #7B8798;
    font-size: 13px;
    margin-bottom: 22px;
}

.section-title {
    font-size: 17px;
    font-weight: 700;
    color: #182943;
    margin: 12px 0 12px 0;
}

.metric-card {
    background: white;
    border: 1px solid #E7ECF3;
    border-radius: 13px;
    padding: 18px 20px;
    min-height: 125px;
    box-shadow: 0 3px 12px rgba(25, 45, 75, 0.035);
}

.metric-label {
    font-size: 12px;
    color: #7B8798;
    font-weight: 600;
    margin-bottom: 12px;
}

.metric-value {
    font-size: 25px;
    font-weight: 800;
    color: #172943;
    letter-spacing: -0.8px;
}

.metric-note {
    font-size: 11px;
    color: #8B97A8;
    margin-top: 7px;
}

.panel {
    background: white;
    border: 1px solid #E7ECF3;
    border-radius: 13px;
    padding: 20px;
    box-shadow: 0 3px 12px rgba(25, 45, 75, 0.035);
}

.status-pill {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    background: #E7F8F3;
    color: #07866F;
}

.footer {
    text-align: center;
    color: #98A2B2;
    font-size: 11px;
    padding: 22px 0 5px 0;
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #E7ECF3;
    border-radius: 12px;
    padding: 15px;
}

div[data-testid="stMetricLabel"] {
    color: #718096;
}

div[data-testid="stMetricValue"] {
    color: #172943;
    font-weight: 800;
}

.stButton button, .stDownloadButton button {
    border-radius: 8px;
    font-weight: 600;
}

.stButton button[kind="primary"] {
    background: #3867F5;
    border-color: #3867F5;
}

[data-testid="stDataFrame"] {
    border: 1px solid #E7ECF3;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# DATA LOADING
# =========================================================

@st.cache_data
def load_data():
    files = {
        "entities": "legal_entities.csv",
        "accounts": "bank_accounts.csv",
        "ledger": "ledger_entries.csv",
        "receivables": "receivables.csv",
        "payables": "payables.csv",
        "forecasts": "cash_flow_forecasts.csv",
        "rates": "currency_rates.csv",
    }

    result = {}

    for key, filename in files.items():
        path = DATA_DIR / filename

        if not path.exists():
            raise FileNotFoundError(str(path))

        result[key] = pd.read_csv(path)

    return result


try:
    data = load_data()
    forecast = build_forecast(scenario="BASE")
    exceptions = detect_exceptions()
    validation = validate_ground_truth()

except Exception as error:
    st.error(f"Unable to load dashboard data: {error}")
    st.info(
        "Check that the generated dataset exists and that "
        "your project dependencies are installed."
    )
    st.stop()


# =========================================================
# HELPERS
# =========================================================

def format_inr(value):
    return f"₹{float(value):,.0f}"


def metric_card(label, value, note=""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_heading(title, subtitle):
    st.markdown(
        f"""
        <div class="top-label">YOTTAFLEX / TREASURY</div>
        <div class="page-title">{title}</div>
        <div class="page-subtitle">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )


def chart_layout(fig, height=370):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=35, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(
            family="Inter",
            color="#718096",
            size=11,
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    fig.update_xaxes(
        showgrid=False,
        linecolor="#E7ECF3",
    )

    fig.update_yaxes(
        gridcolor="#EDF1F6",
        zerolinecolor="#D7DEE9",
    )

    return fig


def download_csv(df, filename, label="Download CSV"):
    st.download_button(
        label=label,
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        use_container_width=False,
    )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div class="brand">💧 Yotta<span>Flex</span></div>
        <div class="brand-sub">LIQUIDITY INTELLIGENCE</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### WORKSPACE")

    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Liquidity Forecast",
            "Scenario Analysis",
            "Exception Monitoring",
            "Data Validation",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown("### FORECAST SETTINGS")

    scenario = st.selectbox(
        "Scenario",
        ["BASE", "DELAYED_RECEIPT", "STRESS"],
        index=0,
    )

    st.divider()

    st.markdown("### SYSTEM INFORMATION")
    st.caption("Reporting currency · INR")
    st.caption("Forecast horizon · 30 days")
    st.caption("Dataset seed · 20261022")

    st.markdown(
        """
        <div style="margin-top:45px; padding:12px;
                    background:#1C2C46; border-radius:10px;">
            <div style="font-size:11px;color:#91A6C3;">
                PLATFORM STATUS
            </div>
            <div style="font-size:13px;color:#55D6B0;
                        font-weight:700;margin-top:5px;">
                ● DATA LOADED
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# SHARED FORECAST VALUES
# =========================================================

selected_forecast = build_forecast(scenario=scenario)

opening_balance = float(
    selected_forecast["opening_inr"].iloc[0]
)

final_balance = float(
    selected_forecast["closing_inr"].iloc[-1]
)

minimum_balance = float(
    selected_forecast["closing_inr"].min()
)

passed = int((validation["result"] == "PASS").sum())
failed = int((validation["result"] == "FAIL").sum())


# =========================================================
# TOP HEADER
# =========================================================

left, right = st.columns([4, 1])

with left:
    st.markdown(
        '<span class="status-pill">● SYNTHETIC DATA ENVIRONMENT</span>',
        unsafe_allow_html=True,
    )

with right:
    st.markdown(
        "<div style='text-align:right;color:#7B8798;"
        "font-size:12px;padding-top:5px;'>"
        "TREASURY CONTROL CENTER"
        "</div>",
        unsafe_allow_html=True,
    )

st.write("")


# =========================================================
# 1. OVERVIEW
# =========================================================

if page == "Overview":

    page_heading(
        "Executive Overview",
        "A consolidated view of cash positions, liquidity projections and financial risk.",
    )

    # KPI CARDS

    cols = st.columns(4)

    with cols[0]:
        metric_card(
            "LEGAL ENTITIES",
            f"{len(data['entities']):,}",
            "Entities in the dataset",
        )

    with cols[1]:
        metric_card(
            "BANK ACCOUNTS",
            f"{len(data['accounts']):,}",
            "Connected synthetic accounts",
        )

    with cols[2]:
        metric_card(
            "LEDGER ENTRIES",
            f"{len(data['ledger']):,}",
            "Historical financial records",
        )

    with cols[3]:
        metric_card(
            "FORECAST ITEMS",
            f"{len(data['forecasts']):,}",
            "Expected cash flow records",
        )

    st.write("")

    # LIQUIDITY POSITION

    st.markdown(
        '<div class="section-title">30-Day Liquidity Position</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(3)

    with cols[0]:
        metric_card(
            "OPENING LIQUIDITY",
            format_inr(opening_balance),
            "Starting projected position",
        )

    with cols[1]:
        metric_card(
            "PROJECTED CLOSING",
            format_inr(final_balance),
            f"Scenario: {scenario}",
        )

    with cols[2]:
        metric_card(
            "MINIMUM PROJECTED BALANCE",
            format_inr(minimum_balance),
            "Lowest daily closing balance",
        )

    st.write("")

    # CHART AND ALERTS

    chart_col, alert_col = st.columns([2.2, 1])

    with chart_col:

        with st.container(border=True):

            st.markdown("#### Projected Cash Position")

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=selected_forecast["date"],
                    y=selected_forecast["closing_inr"],
                    mode="lines",
                    name="Closing balance",
                    line=dict(color=BLUE, width=3),
                    fill="tozeroy",
                    fillcolor="rgba(56,103,245,0.08)",
                )
            )

            fig.add_hline(
                y=0,
                line_dash="dash",
                line_color="#E35D6A",
            )

            fig = chart_layout(fig, 350)

            fig.update_yaxes(title="INR")
            fig.update_xaxes(title="Forecast date")

            st.plotly_chart(fig, use_container_width=True)

    with alert_col:

        with st.container(border=True):

            st.markdown("#### Risk & Controls")

            st.metric(
                "Detected Exceptions",
                f"{len(exceptions):,}",
            )

            st.metric(
                "Validation Passed",
                f"{passed}/{len(validation)}",
            )

            st.metric(
                "Validation Failed",
                failed,
            )

            if failed == 0:
                st.success("Ground-truth validation passed")
            else:
                st.error("Validation issues detected")

            if minimum_balance < 0:
                st.warning("Potential liquidity shortfall detected.")
            else:
                st.success("No negative daily closing balance in this scenario.")

    # DATA SUMMARY

    st.markdown(
        '<div class="section-title">Financial Data Inventory</div>',
        unsafe_allow_html=True,
    )

    inventory = pd.DataFrame(
        [
            ["Legal Entities", len(data["entities"])],
            ["Bank Accounts", len(data["accounts"])],
            ["Ledger Entries", len(data["ledger"])],
            ["Receivables", len(data["receivables"])],
            ["Payables", len(data["payables"])],
            ["Cash Flow Forecasts", len(data["forecasts"])],
            ["Currency Rates", len(data["rates"])],
        ],
        columns=["Data Source", "Records"],
    )

    st.dataframe(
        inventory,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# 2. LIQUIDITY FORECAST
# =========================================================

elif page == "Liquidity Forecast":

    page_heading(
        "Liquidity Forecast",
        "Daily projected cash position over the next 30 days.",
    )

    cols = st.columns(3)

    with cols[0]:
        metric_card(
            "OPENING BALANCE",
            format_inr(opening_balance),
        )

    with cols[1]:
        metric_card(
            "CLOSING BALANCE",
            format_inr(final_balance),
        )

    with cols[2]:
        metric_card(
            "MINIMUM BALANCE",
            format_inr(minimum_balance),
        )

    st.write("")

    with st.container(border=True):

        st.markdown("#### Daily Liquidity Projection")

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=selected_forecast["date"],
                y=selected_forecast["closing_inr"],
                name="Closing",
                mode="lines+markers",
                line=dict(color=BLUE, width=3),
                marker=dict(size=5),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=selected_forecast["date"],
                y=selected_forecast["opening_inr"],
                name="Opening",
                mode="lines",
                line=dict(color=TEAL, width=2, dash="dot"),
            )
        )

        fig.add_hline(
            y=0,
            line_dash="dash",
            line_color="#E35D6A",
        )

        fig = chart_layout(fig, 420)

        fig.update_yaxes(title="INR")
        fig.update_xaxes(title="Date")

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Daily Forecast Records")

    display_forecast = selected_forecast.copy()

    st.dataframe(
        display_forecast,
        use_container_width=True,
        hide_index=True,
    )

    download_csv(
        selected_forecast,
        f"liquidity_forecast_{scenario.lower()}.csv",
        "↓ Download Forecast CSV",
    )


# =========================================================
# 3. SCENARIO ANALYSIS
# =========================================================

elif page == "Scenario Analysis":

    page_heading(
        "Scenario Analysis",
        "Understand how delayed receipts and financial stress affect future liquidity.",
    )

    scenario_names = [
        "BASE",
        "DELAYED_RECEIPT",
        "STRESS",
    ]

    scenario_frames = {
        name: build_forecast(name)
        for name in scenario_names
    }

    scenario_data = pd.concat(
        scenario_frames.values(),
        ignore_index=True,
    )

    with st.container(border=True):

        st.markdown("#### Scenario Comparison")

        fig = px.line(
            scenario_data,
            x="date",
            y="closing_inr",
            color="scenario",
            markers=True,
            color_discrete_map={
                "BASE": BLUE,
                "DELAYED_RECEIPT": TEAL,
                "STRESS": "#E35D6A",
            },
        )

        fig.add_hline(
            y=0,
            line_dash="dash",
            line_color="#AAB4C2",
        )

        fig = chart_layout(fig, 420)

        fig.update_yaxes(title="Closing balance (INR)")
        fig.update_xaxes(title="Forecast date")

        st.plotly_chart(fig, use_container_width=True)

    comparison = []

    for name, df in scenario_frames.items():

        comparison.append(
            {
                "Scenario": name,
                "Opening Balance": df["opening_inr"].iloc[0],
                "Final Closing Balance": df["closing_inr"].iloc[-1],
                "Minimum Balance": df["closing_inr"].min(),
            }
        )

    comparison_df = pd.DataFrame(comparison)

    st.markdown("#### Scenario Summary")

    st.dataframe(
        comparison_df.style.format(
            {
                "Opening Balance": "₹{:,.0f}",
                "Final Closing Balance": "₹{:,.0f}",
                "Minimum Balance": "₹{:,.0f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    download_csv(
        comparison_df,
        "scenario_comparison.csv",
        "↓ Download Scenario Comparison",
    )

    st.write("")

    if comparison_df["Minimum Balance"].min() < 0:
        st.warning(
            "At least one modeled scenario produces a negative "
            "daily closing balance. This indicates a potential "
            "liquidity shortfall under the scenario assumptions."
        )


# =========================================================
# 4. EXCEPTION MONITORING
# =========================================================

elif page == "Exception Monitoring":

    page_heading(
        "Exception Monitoring",
        "Identify data-quality issues and unusual financial records.",
    )

    st.markdown("#### Exception Summary")

    st.metric(
        "Total Detected Exceptions",
        len(exceptions),
    )

    if exceptions.empty:

        st.success("No exceptions detected in the normal dataset.")

    else:

        with st.container(border=True):

            st.markdown("#### Detected Exceptions")

            st.dataframe(
                exceptions,
                use_container_width=True,
                hide_index=True,
            )

            download_csv(
                exceptions,
                "liquidity_exceptions.csv",
                "↓ Download Exception Report",
            )

    st.info(
        "The five synthetic anomaly fixtures are maintained separately "
        "from the normal generated financial dataset. They are used "
        "for controlled detection and validation."
    )


# =========================================================
# 5. DATA VALIDATION
# =========================================================

elif page == "Data Validation":

    page_heading(
        "Data Validation",
        "Compare detected anomalies against the expected ground truth.",
    )

    cols = st.columns(3)

    with cols[0]:
        metric_card(
            "TOTAL CHECKS",
            len(validation),
            "Expected anomaly checks",
        )

    with cols[1]:
        metric_card(
            "PASSED",
            passed,
            "Correctly detected cases",
        )

    with cols[2]:
        metric_card(
            "FAILED",
            failed,
            "Validation mismatches",
        )

    st.write("")

    if failed == 0:
        st.success("All ground-truth validation checks passed.")
    else:
        st.error("Some ground-truth validation checks failed.")

    with st.container(border=True):

        st.markdown("#### Validation Results")

        st.dataframe(
            validation,
            use_container_width=True,
            hide_index=True,
        )

        download_csv(
            validation,
            "ground_truth_validation.csv",
            "↓ Download Validation Report",
        )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.markdown(
    """
    <div class="footer">
        YOTTAFLEX LIQUIDITY INTELLIGENCE PLATFORM
        <br>
        Treasury Analytics · Synthetic Financial Data · INR Reporting
        <br>
        30-Day Liquidity Forecasting & Risk Monitoring
    </div>
    """,
    unsafe_allow_html=True,
)
