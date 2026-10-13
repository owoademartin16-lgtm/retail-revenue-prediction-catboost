"""Retail Sales Intelligence — daily sales forecast.

Loads the pre-trained artifacts from "Business Sales.ipynb":
  - Business Sales.joblib  ({'model': CatBoostRegressor, 'features': [...]})
    Features: time_index, Month, Day, DayOfWeek, IsWeekend, is_q4,
    is_month_start, is_month_end, lag_1d, lag_7d, lag_14d, lag_30d,
    rolling_mean_7d, rolling_mean_30d (trained on 296 daily totals,
    R² 0.8652 on the last 60 days).

Pipeline (exactly as trained — never retrained here):
  Date + Recent Sales -> Calendar Features -> DataFrame in exact
  feature order -> Saved CatBoost Model -> Predicted Sales -> Demand Band

Run with:
    streamlit run business_sales_app.py
"""

import calendar
import datetime

import joblib
import pandas as pd
import streamlit as st

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
MODEL_PATH = "Business Sales.joblib"

# First modeled day in training (2025-07-01 has time_index 0 after the
# 30-day lag warmup). Later dates continue the same count.
REFERENCE_START_DATE = datetime.date(2025, 7, 1)

# Demand bands from the training daily totals (quartiles of 326 days):
# Q1 $17,975.62, median $24,413.51, Q3 $36,475.40, mean $32,153.71.
QUIET_BELOW = 17975.62
PEAK_ABOVE = 36475.40
TYPICAL_DAY = 32153.71


@st.cache_resource
def load_assets():
    """Load model + feature list once; raises FileNotFoundError."""
    artifacts = joblib.load(MODEL_PATH)
    return artifacts["model"], list(artifacts["features"])


def build_input_df(selected_date, lag_1d, lag_7d, lag_14d, lag_30d,
                    rolling_mean_7d, rolling_mean_30d, features):
    """One row in exact training column order; calendar parts are automatic."""
    weekday = selected_date.weekday()  # Monday=0
    row = {
        "time_index": max(0, (selected_date - REFERENCE_START_DATE).days),
        "Month": selected_date.month,
        "Day": selected_date.day,
        "DayOfWeek": weekday,
        "IsWeekend": 1 if weekday >= 5 else 0,
        "is_q4": 1 if selected_date.month in (10, 11, 12) else 0,
        "is_month_start": 1 if selected_date.day <= 3 else 0,
        "is_month_end": 1 if selected_date.day >= 28 else 0,
        "lag_1d": float(lag_1d),
        "lag_7d": float(lag_7d),
        "lag_14d": float(lag_14d),
        "lag_30d": float(lag_30d),
        "rolling_mean_7d": float(rolling_mean_7d),
        "rolling_mean_30d": float(rolling_mean_30d),
    }
    return pd.DataFrame([[row[f] for f in features]], columns=features)


def predict_sales(model, input_df):
    """Predict and floor at zero (sales can't be negative)."""
    return max(0.0, float(model.predict(input_df)[0]))


def demand_band(prediction):
    """Map predicted sales to a Quiet / Steady / Peak demand band."""
    if prediction < QUIET_BELOW:
        return "Quiet Day"
    if prediction <= PEAK_ABOVE:
        return "Steady Day"
    return "Peak Day"


# Retail theme: deep-violet hero, gold accents, soft colorful cards.
THEME_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] {
    font-family: 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
}
.hero {
    background: linear-gradient(120deg, #2E1065 0%, #6D28D9 60%, #A78BFA 100%);
    border-radius: 18px;
    padding: 2rem 2.2rem;
    color: #FFFFFF;
    box-shadow: 0 12px 32px rgba(46, 16, 101, 0.35);
    margin-bottom: 1.2rem;
}
.hero h1 {
    font-family: 'Playfair Display', Georgia, serif !important;
    color: #FFFFFF !important;
    margin: 0 0 0.3rem !important;
    font-size: 2.4rem !important;
}
.hero p { color: #EDE9FE !important; margin: 0; font-size: 1.05rem; }
.hero .gold-rule {
    width: 72px; height: 4px; border-radius: 4px;
    background: linear-gradient(90deg, #D4AF37, #F6E27A);
    margin-bottom: 0.9rem;
}
div.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #6D28D9, #A78BFA);
    border: none; color: #FFFFFF !important;
    font-weight: 800; font-size: 1.05rem;
    border-radius: 12px; padding: 0.7rem 1.4rem; width: 100%;
    box-shadow: 0 6px 18px rgba(109, 40, 217, 0.4);
}
div.stButton > button[kind="primary"]:hover {
    filter: brightness(1.08);
}
.sales-card {
    border-radius: 16px; padding: 1.6rem 1.8rem; color: #FFFFFF;
    box-shadow: 0 10px 26px rgba(0, 0, 0, 0.25);
    text-align: center; margin-bottom: 1rem;
}
.sales-quiet { background: linear-gradient(120deg, #1E3A8A, #60A5FA); }
.sales-steady { background: linear-gradient(120deg, #4C1D95, #A78BFA); }
.sales-peak { background: linear-gradient(120deg, #92400E, #F59E0B); }
.sales-card .label {
    font-size: 0.8rem; font-weight: 700;
    letter-spacing: 0.08em; text-transform: uppercase;
    color: rgba(255, 255, 255, 0.85);
}
.sales-card .value { font-size: 2.6rem; font-weight: 800; margin: 0.1rem 0; }
.sales-card .band {
    display: inline-block; background: rgba(255, 255, 255, 0.25);
    border-radius: 999px; padding: 0.25rem 1.1rem; font-weight: 700;
}
</style>
"""

WEEKDAY_NAMES = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
]


# ------------------------------------------------------------------
# App
# ------------------------------------------------------------------
def main():
    try:
        model, features = load_assets()
    except FileNotFoundError as err:
        st.error(
            "Model file not found. Make sure 'Business Sales.joblib' is in "
            f"the same folder as this script. (Details: {err})"
        )
        st.stop()
    except Exception:
        st.error("Could not load the model file. Check it is valid and try again.")
        st.stop()

    st.set_page_config(
        page_title="Retail Sales Intelligence",
        page_icon="🏬",
        layout="wide",
    )

    # ---- Header ----
    st.markdown(THEME_CSS, unsafe_allow_html=True)
    st.markdown(
        '<div class="hero"><div class="gold-rule"></div>'
        '<div style="display:flex;align-items:center;gap:0.9rem;">'
        '<svg width="52" height="52" viewBox="0 0 64 64" fill="none">'
        "<defs><linearGradient id='gold' x1='0' y1='0' x2='1' y2='1'>"
        "<stop offset='0' stop-color='#F6E27A'/>"
        "<stop offset='1' stop-color='#D4AF37'/></linearGradient></defs>"
        "<path d='M8 24 14 10h36l6 14z' fill='url(#gold)'/>"
        "<rect x='12' y='26' width='40' height='26' rx='3' fill='none' stroke='url(#gold)' stroke-width='4'/>"
        "<line x1='24' y1='32' x2='24' y2='46' stroke='url(#gold)' stroke-width='4' stroke-linecap='round'/>"
        "<line x1='40' y1='32' x2='40' y2='46' stroke='url(#gold)' stroke-width='4' stroke-linecap='round'/>"
        "</svg>"
        "<div><h1 style='margin:0 !important;'>Retail Sales Intelligence</h1>"
        "<p>AI-powered daily sales forecast</p></div>"
        "</div></div>",
        unsafe_allow_html=True,
    )

    # ---- Input sections ----
    with st.container(border=True):
        st.subheader("Forecast Date")
        c1, c2, c3 = st.columns(3)
        with c1:
            year = st.number_input("Year", 2025, 2027, 2026, 1)
        with c2:
            month = st.number_input("Month", 1, 12, 5, 1)
        with c3:
            day = st.number_input("Day", 1, 31, 1, 1)

    with st.container(border=True):
        st.subheader("Recent Daily Sales ($)")
        st.caption("Actual sales on those past days, used for lag features. "
                   "Averages feed the rolling means.")
        r1, r2, r3 = st.columns(3)
        with r1:
            lag_1d = st.number_input("Sales yesterday", 0.0, value=32000.0,
                                     step=500.0)
        with r2:
            lag_7d = st.number_input("Sales 7 days ago", 0.0, value=31000.0,
                                     step=500.0)
        with r3:
            lag_14d = st.number_input("Sales 14 days ago", 0.0, value=30000.0,
                                      step=500.0)
        r4, r5, r6 = st.columns(3)
        with r4:
            lag_30d = st.number_input("Sales 30 days ago", 0.0, value=29000.0,
                                      step=500.0)
        with r5:
            rolling_mean_7d = st.number_input("Average of last 7 days", 0.0,
                                              value=31000.0, step=500.0)
        with r6:
            rolling_mean_30d = st.number_input("Average of last 30 days", 0.0,
                                               value=30000.0, step=500.0)

    predict = st.button("Predict Sales", type="primary")

    # ---- Prediction section ----
    if predict:
        try:
            selected_date = datetime.date(int(year), int(month), int(day))
        except ValueError:
            st.error("Invalid date for that month (e.g. Feb 30 does not exist).")
            st.stop()

        try:
            input_df = build_input_df(
                selected_date, lag_1d, lag_7d, lag_14d, lag_30d,
                rolling_mean_7d, rolling_mean_30d, features,
            )
            prediction = predict_sales(model, input_df)
        except Exception:
            st.error("Could not compute the forecast. "
                     "Check the inputs and try again.")
        else:
            st.divider()
            band = demand_band(prediction)
            card_class = {
                "Quiet Day": "sales-quiet",
                "Steady Day": "sales-steady",
                "Peak Day": "sales-peak",
            }[band]
            weekday = selected_date.weekday()
            _, last_day = calendar.monthrange(selected_date.year,
                                              selected_date.month)
            st.markdown(
                f'<div class="sales-card {card_class}">'
                f'<div class="label">Predicted Daily Sales</div>'
                f'<div class="value">${prediction:,.2f}</div>'
                f'<div>{selected_date.strftime("%A, %B %d, %Y")}</div>'
                f'<div style="margin-top:0.4rem;"><span class="band">'
                f'{band}</span></div>'
                f"</div>",
                unsafe_allow_html=True,
            )
            kind = ("Weekend" if weekday >= 5 else "Weekday")
            st.markdown(
                f"**{WEEKDAY_NAMES[weekday]}** · "
                f"{MONTH_NAMES[selected_date.month - 1]} · {kind} · "
                f"typical day ≈ **${TYPICAL_DAY:,.0f}**"
                + (" · month has "
                   f"{last_day} days" if selected_date.day == last_day else "")
            )
            badge = (
                '<span style="display:inline-block;width:12px;height:12px;'
                "border-radius:3px;background:{color};margin-right:0.45rem;"
                'vertical-align:baseline;"></span>'
            )
            small = "font-size:0.85rem;color:#4B5563;"
            st.markdown(
                "**What the demand bands mean (from training daily totals):**\n\n"
                f"<span style='{small}'>"
                f"{badge.format(color='#60A5FA')}"
                f"{'**' if band == 'Quiet Day' else ''}"
                "Quiet Day (below $17,976), slow day, protect staffing costs"
                f"{'**' if band == 'Quiet Day' else ''}</span>\n\n"
                f"<span style='{small}'>"
                f"{badge.format(color='#A78BFA')}"
                f"{'**' if band == 'Steady Day' else ''}"
                "Steady Day ($17,976 to $36,475), normal trading, standard staffing"
                f"{'**' if band == 'Steady Day' else ''}</span>\n\n"
                f"<span style='{small}'>"
                f"{badge.format(color='#F59E0B')}"
                f"{'**' if band == 'Peak Day' else ''}"
                "Peak Day (above $36,475), stock up and staff up"
                f"{'**' if band == 'Peak Day' else ''}</span>",
                unsafe_allow_html=True,
            )
            if prediction > PEAK_ABOVE:
                st.warning(
                    "Peak demand expected. Consider extra stock and staffing "
                    "for this date."
                )

    # ---- Model section ----
    st.divider()
    with st.expander("About this forecast"):
        st.markdown(
            "**Model**\n\nCatBoost Regressor (R² 0.865 on the last 60 days)\n\n"
            "**Purpose**\n\nPredict next-day total sales revenue"
        )


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------
# Setup
# ------------------------------------------------------------------
# pip install streamlit pandas numpy joblib scikit-learn catboost
# streamlit run business_sales_app.py
