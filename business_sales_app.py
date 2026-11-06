"""Retail Sales Intelligence - a colorful Streamlit dashboard.

Run from this folder:
    streamlit run app.py
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

import charts
import forecast
import theme

st.set_page_config(
    page_title="Retail Sales Intelligence",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = Path(__file__).resolve().parent / "data" / "retail_sales_ml_apl.csv"
DATE_FORMAT = "%d %b %Y"
SALES_TYPE_ORDER = ["Full Price", "Promo", "Markdown Tier 1", "Markdown Tier 2", "Clearance"]

DEMAND_BANDS = [
    {
        "key": "quiet",
        "name": "Quiet Day",
        "range": f"below {theme.money(forecast.QUIET_BELOW, compact=False, decimals=0)}",
        "action": "Slow day, protect staffing costs",
        "headline": "Quiet demand expected.",
        "detail": "Consider protecting staffing costs for this date.",
    },
    {
        "key": "steady",
        "name": "Steady Day",
        "range": (
            f"{theme.money(forecast.QUIET_BELOW, compact=False, decimals=0)} to "
            f"{theme.money(forecast.PEAK_ABOVE, compact=False, decimals=0)}"
        ),
        "action": "Normal trading, standard staffing",
        "headline": "Steady demand expected.",
        "detail": "Normal trading and standard staffing should cover this date.",
    },
    {
        "key": "peak",
        "name": "Peak Day",
        "range": f"above {theme.money(forecast.PEAK_ABOVE, compact=False, decimals=0)}",
        "action": "Stock up and staff up",
        "headline": "Peak demand expected.",
        "detail": "Consider extra stock and staffing for this date.",
    },
]


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    df = df.drop(columns=["Reason of Return"], errors="ignore")
    df["Transaction Date"] = pd.to_datetime(df["Transaction Date"], errors="coerce")
    df = df.dropna(subset=["Transaction Date"]).copy()

    for column in ["Sales Amount", "Cogs", "Qty Sold", "Number of Transactions"]:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0.0)

    df["Is Return"] = df["Is Return"].fillna(0).astype(int)
    df["Revenue"] = df["Sales Amount"]
    df["COGS"] = df["Cogs"]
    df["Gross Profit"] = df["Revenue"] - df["COGS"]
    df["Units"] = df["Qty Sold"]

    df["Month"] = df["Transaction Date"].dt.to_period("M").dt.to_timestamp()
    df["Month Label"] = df["Month"].dt.strftime("%b %Y")
    return df


def make_defaults(df: pd.DataFrame) -> dict:
    min_date = df["Transaction Date"].min().date()
    max_date = df["Transaction Date"].max().date()
    divisions = sorted(df["Product Division"].dropna().unique().tolist())
    categories = sorted(df["Product Category"].dropna().unique().tolist())
    stores = sorted(df["Store"].dropna().unique().tolist())
    channels = sorted(df["Sales Channel"].dropna().unique().tolist())
    available_types = df["Sales Type"].dropna().unique().tolist()
    sales_types = [x for x in SALES_TYPE_ORDER if x in available_types]
    sales_types += [x for x in sorted(available_types) if x not in sales_types]

    return {
        "min_date": min_date,
        "max_date": max_date,
        "divisions": divisions,
        "categories": categories,
        "stores": stores,
        "channels": channels,
        "sales_types": sales_types,
        "date_range": (min_date, max_date),
        "division_filter": "All divisions",
        "category_filter": "All categories",
        "store_filter": "All stores",
        "channel_filter": "All channels",
        "sales_type_filter": sales_types,
        "scope_filter": "All records",
    }


def init_state(defaults: dict) -> None:
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def resolve_dates(date_range, min_date: dt.date, max_date: dt.date) -> tuple[dt.date, dt.date]:
    if isinstance(date_range, (tuple, list)):
        if len(date_range) >= 2:
            return date_range[0] or min_date, date_range[1] or max_date
        if len(date_range) == 1:
            return date_range[0] or min_date, date_range[0] or max_date
    if date_range is None:
        return min_date, max_date
    return date_range, date_range


def filter_data(
    df: pd.DataFrame,
    start_date: dt.date,
    end_date: dt.date,
    division: str,
    category: str,
    store: str,
    channel: str,
    sales_types: list[str],
    scope: str,
) -> pd.DataFrame:
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date) + pd.Timedelta(days=1)
    mask = (df["Transaction Date"] >= start) & (df["Transaction Date"] < end)
    filtered = df.loc[mask].copy()

    if division != "All divisions":
        filtered = filtered[filtered["Product Division"] == division]
    if category != "All categories":
        filtered = filtered[filtered["Product Category"] == category]
    if store != "All stores":
        filtered = filtered[filtered["Store"] == store]
    if channel != "All channels":
        filtered = filtered[filtered["Sales Channel"] == channel]
    if sales_types:
        filtered = filtered[filtered["Sales Type"].isin(sales_types)]

    if scope == "Sales only":
        filtered = filtered[filtered["Is Return"] == 0]
    elif scope == "Returns only":
        filtered = filtered[filtered["Is Return"] == 1]
    return filtered


# ---------------------------------------------------------------------------
# Small view helpers
# ---------------------------------------------------------------------------
def trend_text(current: float, previous: float) -> str:
    if previous is None or previous <= 0:
        return "Current slice"
    change = (current - previous) / previous * 100
    if abs(change) < 0.05:
        return "Flat vs prior period"
    arrow = "▲" if change > 0 else "▼"
    return f"{arrow} {abs(change):.1f}% vs prior period"


def chart_card(title: str, subtitle: str, fig) -> None:
    with st.container(border=True):
        theme.chart_header(title, subtitle)
        st.plotly_chart(
            fig,
            width="stretch",
            theme=None,
            config={"displayModeBar": False, "responsive": True},
        )


def mini_stat(label: str, value: str, sub: str = "") -> str:
    return theme.md(
        f'<div class="mini-stat"><div class="label">{label}</div>'
        f'<div class="value">{value}</div>'
        f'<div class="sub">{sub}</div></div>'
    )


def format_money_table(series: pd.Series) -> pd.Series:
    return series.map(lambda v: theme.money(v, compact=False, decimals=0))


def format_pct_table(series: pd.Series) -> pd.Series:
    return series.map(lambda v: theme.percent(v, decimals=2))


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def render_sidebar(defaults: dict) -> tuple:
    with st.sidebar:
        theme.md(
            """
            <div class="sidebar-brand">
              <div class="sidebar-mark">R</div>
              <div>
                <div class="sidebar-name">Retail Intelligence</div>
                <div class="sidebar-sub">Sales dashboard</div>
              </div>
            </div>
            """
        )

        if st.button("Reset filters", width="stretch"):
            for key, value in defaults.items():
                st.session_state[key] = value
            st.rerun()

        theme.md('<div class="sidebar-heading">Date window</div>')
        date_range = st.date_input(
            "Date range",
            key="date_range",
            min_value=defaults["min_date"],
            max_value=defaults["max_date"],
            format="DD/MM/YYYY",
            label_visibility="collapsed",
        )

        theme.md('<div class="sidebar-heading">Product lens</div>')
        division = st.selectbox(
            "Product division",
            options=["All divisions"] + defaults["divisions"],
            key="division_filter",
        )
        category = st.selectbox(
            "Product category",
            options=["All categories"] + defaults["categories"],
            key="category_filter",
        )

        theme.md('<div class="sidebar-heading">Store and channel</div>')
        store = st.selectbox(
            "Store",
            options=["All stores"] + defaults["stores"],
            key="store_filter",
        )
        channel = st.selectbox(
            "Sales channel",
            options=["All channels"] + defaults["channels"],
            key="channel_filter",
        )

        theme.md('<div class="sidebar-heading">Transaction type</div>')
        sales_types = st.multiselect(
            "Sales type",
            options=defaults["sales_types"],
            key="sales_type_filter",
            placeholder="All sales types",
        )
        scope = st.radio(
            "Scope",
            options=["All records", "Sales only", "Returns only"],
            key="scope_filter",
        )

        theme.md(
            f"""
            <div class="sidebar-note">
              Every chart recalculates from the filters above. Leave sales type
              empty to include every transaction type.
            </div>
            """
        )

    return date_range, division, category, store, channel, sales_types, scope


# ---------------------------------------------------------------------------
# Header and KPIs
# ---------------------------------------------------------------------------
def render_hero(filtered: pd.DataFrame, start_date: dt.date, end_date: dt.date, kpis: dict) -> None:
    records = len(filtered)

    theme.md(
        f"""
        <div class="hero">
          <div class="hero-kicker">retail intelligence / {start_date:{DATE_FORMAT}} to {end_date:{DATE_FORMAT}}</div>
          <h1>Retail Sales Intelligence</h1>
          <p>
            Filter the receipts to see what sells, what stays, and what comes back.
          </p>
          <div class="hero-tags">
            <span class="hero-tag"><b>{records:,}</b> receipts</span>
            <span class="hero-tag"><b>{theme.money(kpis["revenue"])}</b> total revenue</span>
            <span class="hero-tag"><b>{theme.percent(kpis["margin"])}</b> gross margin</span>
            <span class="hero-tag"><b>{theme.percent(kpis["return_rate"])}</b> return rate</span>
          </div>
        </div>
        """
    )


def render_kpis(kpis: dict, revenue_trend: str) -> None:
    cards = [
        theme.kpi_card(
            "Total revenue",
            theme.money(kpis["revenue"]),
            revenue_trend,
            theme.VIOLET,
        ),
        theme.kpi_card(
            "Gross profit",
            theme.money(kpis["profit"]),
            f"{theme.percent(kpis['margin'])} gross margin",
            theme.TEAL,
        ),
        theme.kpi_card(
            "Gross margin",
            theme.percent(kpis["margin"]),
            "Profit after cost of goods",
            theme.BLUE,
        ),
        theme.kpi_card(
            "Transactions",
            f"{kpis['transactions']:,.0f}",
            f"{kpis['units']:,.0f} units sold",
            theme.AMBER,
        ),
        theme.kpi_card(
            "Average order",
            theme.money(kpis["aov"], compact=False, decimals=2),
            f"Across {kpis['records']:,} receipts",
            theme.CORAL,
        ),
        theme.kpi_card(
            "Return rate",
            theme.percent(kpis["return_rate"]),
            f"{theme.money(kpis['returned_value'], compact=False)} returned",
            theme.PINK,
        ),
    ]

    for row in (cards[:3], cards[3:]):
        cols = st.columns(3)
        for col, card in zip(cols, row):
            with col:
                theme.md(card)


def calculate_kpis(filtered: pd.DataFrame) -> dict:
    revenue = float(filtered["Revenue"].sum())
    profit = float(filtered["Gross Profit"].sum())
    transactions = float(len(filtered))
    records = len(filtered)
    returns = filtered[filtered["Is Return"] == 1]
    returned_value = abs(float(returns["Sales Amount"].sum()))
    return {
        "revenue": revenue,
        "profit": profit,
        "margin": (profit / revenue * 100) if revenue else 0.0,
        "transactions": transactions,
        "records": records,
        "units": float(filtered["Units"].sum()),
        "aov": (revenue / transactions) if transactions else 0.0,
        "return_rate": (len(returns) / records * 100) if records else 0.0,
        "returned_value": returned_value,
    }


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
def render_overview(filtered: pd.DataFrame) -> None:
    theme.section(
        "01 / overview",
        "The shape of the business",
        "Monthly momentum, the cost bridge, and the mix that drives revenue.",
    )

    left, right = st.columns([2.05, 1.0])
    with left:
        chart_card(
            "Monthly revenue and gross profit",
            "Bars show revenue for each month. The teal line tracks gross profit.",
            charts.monthly_revenue_chart(filtered),
        )
    with right:
        chart_card(
            "Sales type mix",
            "Share of filtered receipts by transaction type.",
            charts.sales_type_chart(filtered),
        )

    left, right = st.columns([1.12, 1.0])
    with left:
        chart_card(
            "Revenue to profit bridge",
            "Total revenue, cost of goods, and the gross profit left behind.",
            charts.profit_bridge_chart(filtered),
        )
    with right:
        chart_card(
            "Division split",
            "Revenue share by product division, based on total revenue in the current slice.",
            charts.division_chart(filtered),
        )

    by_category = filtered.groupby("Product Category", observed=True)["Revenue"].sum()
    by_month = filtered.groupby("Month", observed=True)["Revenue"].sum()
    top_category = by_category.idxmax() if not by_category.empty else "No category"
    top_category_value = by_category.max() if not by_category.empty else 0.0
    peak_month = by_month.idxmax() if not by_month.empty else None
    peak_month_value = by_month.max() if not by_month.empty else 0.0
    month_text = peak_month.strftime("%B %Y") if peak_month is not None else "No month"

    theme.md(
        f"""
        <div class="insight">
          <strong>{top_category}</strong> leads this slice with
          {theme.money(top_category_value)} in total revenue.
          <strong>{month_text}</strong> is the strongest month at
          {theme.money(peak_month_value)}. Use the tabs to move from the
          headline to products, stores, time and returns.
        </div>
        """
    )


def render_products(filtered: pd.DataFrame) -> None:
    theme.section(
        "02 / products",
        "What customers keep buying",
        "Rank categories by revenue, then read the margin and return profile behind each one.",
    )

    chart_card(
        "Top categories by total revenue",
        "Color marks the division: violet for Scholar, coral for Femme, teal for Junior.",
        charts.category_revenue_chart(filtered, top_n=10),
    )

    cat = (
        filtered.groupby("Product Category", observed=True)
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Gross Profit", "sum"),
            Receipts=("Is Return", "size"),
        )
        .reset_index()
    )
    returns = filtered[filtered["Is Return"] == 1]
    return_counts = returns.groupby("Product Category", observed=True).size()
    cat["Returned"] = cat["Product Category"].map(return_counts).fillna(0).astype(int)
    cat["Margin"] = np.where(cat["Revenue"] != 0, cat["Profit"] / cat["Revenue"] * 100, 0.0)
    cat["Return rate"] = np.where(cat["Receipts"] > 0, cat["Returned"] / cat["Receipts"] * 100, 0.0)

    left, right = st.columns([2.0, 1.0])
    with left:
        with st.container(border=True):
            theme.chart_header(
                "Category economics",
                "Top 10 categories in the current filter. Revenue is the sum of Sales Amount; profit is revenue minus COGS.",
            )
            table = cat.nlargest(10, "Revenue").copy()
            display = pd.DataFrame(
                {
                    "Category": table["Product Category"],
                    "Total revenue": format_money_table(table["Revenue"]),
                    "Gross profit": format_money_table(table["Profit"]),
                    "Margin": format_pct_table(table["Margin"]),
                    "Return rate": format_pct_table(table["Return rate"]),
                }
            )
            st.dataframe(display, hide_index=True, width="stretch")

    with right:
        with st.container(border=True):
            theme.chart_header("Category signals", "Three quick reads from the same filter.")
            if cat.empty:
                st.info("No category data in this slice.")
            else:
                best_margin = cat[cat["Revenue"] > 0].sort_values("Margin", ascending=False).head(1)
                return_leader = cat.sort_values("Return rate", ascending=False).head(1)
                top = cat.sort_values("Revenue", ascending=False).head(1).iloc[0]
                mini_stat("Top category", charts.short_category(top["Product Category"]), theme.money(top["Revenue"]))
                if not best_margin.empty:
                    bm = best_margin.iloc[0]
                    mini_stat("Best margin", charts.short_category(bm["Product Category"]), theme.percent(bm["Margin"]))
                if not return_leader.empty:
                    rl = return_leader.iloc[0]
                    mini_stat("Highest return rate", charts.short_category(rl["Product Category"]), theme.percent(rl["Return rate"]))

    with st.expander("Show every category"):
        all_cat = cat.sort_values("Revenue", ascending=False).copy()
        all_display = pd.DataFrame(
            {
                "Category": all_cat["Product Category"],
                "Total revenue": format_money_table(all_cat["Revenue"]),
                "Gross profit": format_money_table(all_cat["Profit"]),
                "Margin": format_pct_table(all_cat["Margin"]),
                "Receipts": all_cat["Receipts"].map(lambda v: f"{v:,.0f}"),
                "Returns": all_cat["Returned"].map(lambda v: f"{v:,.0f}"),
                "Return rate": format_pct_table(all_cat["Return rate"]),
            }
        )
        st.dataframe(all_display, hide_index=True, width="stretch")


def render_stores(filtered: pd.DataFrame) -> None:
    theme.section(
        "03 / stores",
        "Where the money lands",
        "Compare store revenue and margin, then look for the outliers hiding in the list.",
    )
    theme.md('<span class="stores-layout" style="display:none"></span>')

    left, right = st.columns([2.05, 1.0])
    with left:
        chart_card(
            "Top stores by total revenue",
            "The top two stores are highlighted. Hover for profit, margin and transactions.",
            charts.store_chart(filtered, top_n=10),
        )
    with right:
        with st.container(border=True):
            theme.chart_header("Store signals", "Read the top of the distribution.")
            store = (
                filtered.groupby("Store", observed=True)
                .agg(
                    Revenue=("Revenue", "sum"),
                    Profit=("Gross Profit", "sum"),
                    Receipts=("Is Return", "size"),
                )
                .reset_index()
            )
            store["Margin"] = np.where(store["Revenue"] != 0, store["Profit"] / store["Revenue"] * 100, 0.0)
            if store.empty:
                st.info("No store data in this slice.")
            else:
                top = store.sort_values("Revenue", ascending=False).head(1).iloc[0]
                best = store[store["Revenue"] > 0].sort_values("Margin", ascending=False).head(1)
                mini_stat("Top store", top["Store"], theme.money(top["Revenue"]))
                if not best.empty:
                    b = best.iloc[0]
                    mini_stat("Best margin", b["Store"], theme.percent(b["Margin"]))
                counts = filtered.groupby("Store", observed=True).size()
                if not counts.empty:
                    busiest = counts.idxmax()
                    mini_stat("Most transactions", busiest, f"{counts.max():,.0f} receipts")

    with st.container(border=True):
        theme.chart_header(
            "Store economics",
            "Top 10 stores in the current filter. Revenue is the sum of Sales Amount; profit is revenue minus COGS.",
        )
        store_table = (
            filtered.groupby("Store", observed=True)
            .agg(
                Revenue=("Revenue", "sum"),
                Profit=("Gross Profit", "sum"),
                Receipts=("Is Return", "size"),
            )
            .reset_index()
            .nlargest(10, "Revenue")
        )
        store_table["Margin"] = np.where(
            store_table["Revenue"] != 0,
            store_table["Profit"] / store_table["Revenue"] * 100,
            0.0,
        )
        display = pd.DataFrame(
            {
                "Store": store_table["Store"],
                "Total revenue": format_money_table(store_table["Revenue"]),
                "Gross profit": format_money_table(store_table["Profit"]),
                "Margin": format_pct_table(store_table["Margin"]),
                "Transactions": store_table["Receipts"].map(lambda v: f"{v:,.0f}"),
            }
        )
        st.dataframe(display, hide_index=True, width="stretch")


def render_time(filtered: pd.DataFrame) -> None:
    theme.section(
        "04 / time",
        "When the business moves",
        "Weekly rhythm, monthly peaks, and the categories that carry a chosen month.",
    )

    monthly = (
        filtered.groupby("Month", observed=True)
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Gross Profit", "sum"),
            Receipts=("Is Return", "size"),
        )
        .reset_index()
        .sort_values("Month")
        .reset_index(drop=True)
    )
    if monthly.empty:
        st.info("No monthly data in this slice.")
        return

    peak_idx = int(monthly["Revenue"].idxmax())

    left, right = st.columns([2.05, 1.0])
    with left:
        chart_card(
            "Weekly total revenue",
            "Each point is a week ending Sunday. The peak week is labelled.",
            charts.weekly_revenue_chart(filtered),
        )
    with right:
        with st.container(border=True):
            theme.chart_header("Month spotlight", "Pick a month to rank its categories.")
            selected_month = st.selectbox(
                "Spotlight month",
                options=monthly["Month"].tolist(),
                index=peak_idx,
                format_func=lambda value: pd.Timestamp(value).strftime("%B %Y"),
                label_visibility="collapsed",
            )
            chosen = monthly[monthly["Month"] == selected_month].iloc[0]
            margin = (chosen["Profit"] / chosen["Revenue"] * 100) if chosen["Revenue"] else 0.0
            mini_stat("Total revenue", theme.money(chosen["Revenue"]), f"{chosen['Receipts']:,.0f} receipts")
            mini_stat("Gross profit", theme.money(chosen["Profit"]), f"{theme.percent(margin)} margin")

    chart_card(
        "Month spotlight categories",
        f"Top categories in {pd.Timestamp(selected_month).strftime('%B %Y')}.",
        charts.month_spotlight_chart(filtered, selected_month),
    )

    with st.container(border=True):
        theme.chart_header("Monthly performance", "Every month in the current filter.")
        display = pd.DataFrame(
            {
                "Month": monthly["Month"].dt.strftime("%b %Y"),
                "Total revenue": format_money_table(monthly["Revenue"]),
                "Gross profit": format_money_table(monthly["Profit"]),
                "Margin": (monthly["Profit"] / monthly["Revenue"].replace(0, np.nan) * 100).fillna(0).map(
                    lambda v: theme.percent(v)
                ),
            }
        )
        st.dataframe(
            display.iloc[::-1],
            hide_index=True,
            width="stretch",
            height=min(460, 36 * (len(display) + 1) + 2),
        )


def render_returns(filtered: pd.DataFrame) -> None:
    theme.section(
        "05 / returns",
        "What comes back",
        "Returned revenue and lost profit, split by division and product category.",
    )

    returns = filtered[filtered["Is Return"] == 1]
    if returns.empty:
        st.info(
            "No returned records in this slice. Set the scope to All records or "
            "Returns only to inspect the return profile."
        )
        return

    returned_value = abs(float(returns["Sales Amount"].sum()))
    lost_profit = abs(float(returns["Gross Profit"].sum()))
    lost_profit_display = round(lost_profit, 1)
    return_rate = len(returns) / len(filtered) * 100 if len(filtered) else 0.0
    stats = [
        ("Returned records", f"{len(returns):,.0f}", "Receipts flagged as returns"),
        ("Returned revenue", theme.money(returned_value, compact=False), "Removed from net sales"),
        ("Lost profit", theme.money(lost_profit_display, compact=False), "Gross profit removed"),
        ("Return rate", theme.percent(return_rate), "Returns as a share of filtered receipts"),
    ]
    cols = st.columns(4)
    for col, (label, value, sub) in zip(cols, stats):
        with col:
            mini_stat(label, value, sub)

    left, right = st.columns(2)
    with left:
        chart_card(
            "Returns by division",
            "Returned revenue and lost profit, shown as positive amounts.",
            charts.return_division_chart(filtered),
        )
    with right:
        chart_card(
            "Most returned categories",
            "Top categories by returned revenue in the current filter.",
            charts.return_category_chart(filtered, top_n=8),
        )

    totals = (
        filtered.groupby("Product Category", observed=True)
        .agg(
            Receipts=("Is Return", "size"),
            Revenue=("Revenue", "sum"),
        )
        .reset_index()
    )
    returned = (
        returns.groupby("Product Category", observed=True)
        .agg(
            Returns=("Is Return", "size"),
            Returned=("Sales Amount", lambda values: abs(values.sum())),
            Lost=("Gross Profit", lambda values: abs(values.sum())),
        )
        .reset_index()
    )
    table = totals.merge(returned, on="Product Category", how="left").fillna(0)
    table["Return rate"] = np.where(table["Receipts"] > 0, table["Returns"] / table["Receipts"] * 100, 0.0)
    table = table.sort_values("Returned", ascending=False)

    with st.container(border=True):
        theme.chart_header(
            "Return profile by category",
            "Top 10 categories by returned revenue. Return rate compares returns with all receipts in that category.",
        )
        display = pd.DataFrame(
            {
                "Category": table["Product Category"].head(10),
                "Returned revenue": format_money_table(table["Returned"].head(10)),
                "Lost profit": format_money_table(table["Lost"].head(10)),
                "Returns": table["Returns"].head(10).map(lambda v: f"{v:,.0f}"),
                "Return rate": format_pct_table(table["Return rate"].head(10)),
                "Total revenue": format_money_table(table["Revenue"].head(10)),
            }
        )
        st.dataframe(display, hide_index=True, width="stretch")
        st.caption(
            "Return rows carry negative amounts in the CSV. The table shows the "
            "absolute value removed."
        )

    top = table.iloc[0]
    theme.md(
        f"""
        <div class="insight">
          <strong>{top['Product Category']}</strong> accounts for the largest
          returned value in this slice at {theme.money(top['Returned'])}.
          Return rows removed {theme.money(returned_value, compact=False)} from
          net sales and {theme.money(lost_profit_display, compact=False)} from
          gross profit overall.
        </div>
        """
    )


@st.cache_resource(show_spinner=False)
def get_model():
    return forecast.load_assets()


def render_demand_bands(active_band: str | None = None) -> None:
    active_key = forecast.band_class(active_band) if active_band else ""
    rows = []
    for item in DEMAND_BANDS:
        active = " active" if item["key"] == active_key else ""
        rows.append(
            f'<div class="band-row {item["key"]}{active}">'
            '<span class="band-dot"></span>'
            f'<span class="band-name">{item["name"]}</span>'
            f'<span class="band-range">({item["range"]})</span>'
            f'<span class="band-action">{item["action"]}</span>'
            "</div>"
        )
    note = (
        ""
        if active_key
        else '<div class="band-panel-note">Run a forecast to highlight the expected band.</div>'
    )
    theme.md(
        f"""
        <div class="band-panel">
          <div class="band-panel-title">What the demand bands mean</div>
          <div class="band-panel-sub">From training daily totals</div>
          <div class="band-list">
            {''.join(rows)}
          </div>
          {note}
        </div>
        """
    )


def render_forecast(filtered: pd.DataFrame, full_df: pd.DataFrame) -> None:
    theme.section(
        "06 / forecast",
        "Tomorrow, roughly",
        "The saved CatBoost model turns recent daily sales into a next-day revenue estimate.",
    )

    try:
        model, features = get_model()
        model_ready = True
    except Exception as exc:
        model_ready = False
        st.error(f"The forecast model could not be loaded: {exc}")

    if not model_ready:
        return

    st.markdown("#### Run a forecast")
    theme.md(
        '<div class="sidebar-note" style="margin-top:4px; margin-bottom:8px;">'
        "Defaults come from the last 30 days in the current filter. "
        "Adjust any input to test a scenario."
        "</div>"
    )
    sales_daily = (
        filtered.groupby("Transaction Date", observed=True)["Revenue"]
        .sum()
        .sort_index()
    )
    if sales_daily.empty or (filtered["Is Return"] == 1).all():
        sales_daily = (
            full_df.groupby("Transaction Date", observed=True)["Revenue"]
            .sum()
            .sort_index()
        )
    if sales_daily.empty:
        st.info("Not enough daily sales to build a forecast.")
        return

    last_date = sales_daily.index.max().date()
    default_date = last_date + dt.timedelta(days=1)
    average = float(sales_daily.mean())

    def past_value(days_back: int) -> float:
        if len(sales_daily) >= days_back:
            return float(sales_daily.iloc[-days_back])
        return average

    def trailing_mean(window: int) -> float:
        if len(sales_daily) >= window:
            return float(sales_daily.iloc[-window:].mean())
        return average

    with st.form("forecast_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            selected_date = st.date_input(
                "Forecast date",
                value=default_date,
                min_value=dt.date(2025, 1, 1),
                max_value=dt.date(2027, 12, 31),
            )
        with c2:
            lag_1d = st.number_input(
                "Sales yesterday",
                min_value=0.0,
                value=past_value(1),
                step=500.0,
                format="%.2f",
            )
        with c3:
            lag_7d = st.number_input(
                "Sales 7 days ago",
                min_value=0.0,
                value=past_value(7),
                step=500.0,
                format="%.2f",
            )

        c4, c5, c6 = st.columns(3)
        with c4:
            lag_14d = st.number_input(
                "Sales 14 days ago",
                min_value=0.0,
                value=past_value(14),
                step=500.0,
                format="%.2f",
            )
        with c5:
            lag_30d = st.number_input(
                "Sales 30 days ago",
                min_value=0.0,
                value=past_value(30),
                step=500.0,
                format="%.2f",
            )
        with c6:
            rolling_mean_7d = st.number_input(
                "Average of last 7 days",
                min_value=0.0,
                value=trailing_mean(7),
                step=500.0,
                format="%.2f",
            )

        c7, c8 = st.columns([1, 1])
        with c7:
            rolling_mean_30d = st.number_input(
                "Average of last 30 days",
                min_value=0.0,
                value=trailing_mean(30),
                step=500.0,
                format="%.2f",
            )
        with c8:
            pass

        submitted = st.form_submit_button("Run forecast", type="primary", width="stretch")

    if submitted:
        try:
            input_df = forecast.build_input_df(
                selected_date,
                lag_1d,
                lag_7d,
                lag_14d,
                lag_30d,
                rolling_mean_7d,
                rolling_mean_30d,
                features,
            )
            prediction = forecast.predict_sales(model, input_df)
            band = forecast.demand_band(prediction)
            st.session_state["forecast_result"] = {
                "date": selected_date,
                "prediction": prediction,
                "band": band,
            }
        except Exception as exc:
            st.error(f"Could not compute the forecast: {exc}")

    result = st.session_state.get("forecast_result")
    active_band = None
    if result:
        band = str(result["band"]).title()
        active_band = band
        css_class = forecast.band_class(band)
        selected_date = result["date"]
        prediction = result["prediction"]
        weekday = selected_date.strftime("%A")
        month_name = selected_date.strftime("%B")
        day_type = "Weekend" if selected_date.weekday() >= 5 else "Weekday"
        typical_day = theme.money(forecast.TYPICAL_DAY, compact=False, decimals=0)
        meta_parts = [
            f"<strong>{weekday}</strong>",
            f"<strong>{month_name}</strong>",
            day_type,
            f"typical day ≈ <strong>{typical_day}</strong>",
        ]
        meta_html = ' <span class="forecast-meta-sep">·</span> '.join(
            f"<span>{part}</span>" for part in meta_parts
        )
        theme.md(
            f"""
            <div class="forecast-card {css_class}">
              <div class="forecast-label">Predicted daily sales</div>
              <div class="forecast-value">{theme.money(prediction, compact=False, decimals=2)}</div>
              <div class="forecast-date">{weekday}, {selected_date:{DATE_FORMAT}}</div>
              <div class="forecast-band">{band}</div>
            </div>
            <div class="forecast-meta">{meta_html}</div>
            """
        )

    render_demand_bands(active_band)

    if result:
        active_item = next(
            (item for item in DEMAND_BANDS if item["key"] == forecast.band_class(active_band)),
            DEMAND_BANDS[1],
        )
        theme.md(
            f"""
            <div class="demand-callout {active_item['key']}">
              <strong>{active_item['headline']}</strong> {active_item['detail']}
            </div>
            """
        )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
def main() -> None:
    theme.md(theme.CSS)

    if not DATA_PATH.exists():
        st.error(f"Dataset not found at {DATA_PATH}.")
        st.stop()

    df = load_data(str(DATA_PATH))
    defaults = make_defaults(df)
    init_state(defaults)

    date_range, division, category, store, channel, sales_types, scope = render_sidebar(defaults)
    start_date, end_date = resolve_dates(date_range, defaults["min_date"], defaults["max_date"])
    if end_date < start_date:
        start_date, end_date = end_date, start_date

    filtered = filter_data(
        df,
        start_date,
        end_date,
        division,
        category,
        store,
        channel,
        sales_types,
        scope,
    )

    if filtered.empty:
        st.warning(
            "No records match this filter combination. Try widening the date range "
            "or using Reset filters in the sidebar."
        )
        st.stop()

    filter_signature = (
        start_date,
        end_date,
        division,
        category,
        store,
        channel,
        tuple(sales_types),
        scope,
    )
    if st.session_state.get("filter_signature") != filter_signature:
        st.session_state["filter_signature"] = filter_signature
        st.session_state.pop("forecast_result", None)

    kpis = calculate_kpis(filtered)
    period_days = (end_date - start_date).days + 1
    previous_end = start_date - dt.timedelta(days=1)
    previous_start = previous_end - dt.timedelta(days=period_days - 1)
    previous = filter_data(
        df,
        previous_start,
        previous_end,
        division,
        category,
        store,
        channel,
        sales_types,
        scope,
    )
    previous_revenue = float(previous["Revenue"].sum()) if not previous.empty else 0.0

    render_hero(filtered, start_date, end_date, kpis)
    render_kpis(kpis, trend_text(kpis["revenue"], previous_revenue))

    tab_overview, tab_products, tab_stores, tab_time, tab_returns, tab_forecast = st.tabs(
        ["Overview", "Products", "Stores", "Time", "Returns", "Forecast"]
    )

    with tab_overview:
        render_overview(filtered)
    with tab_products:
        render_products(filtered)
    with tab_stores:
        render_stores(filtered)
    with tab_time:
        render_time(filtered)
    with tab_returns:
        render_returns(filtered)
    with tab_forecast:
        render_forecast(filtered, df)


if __name__ == "__main__":
    main()
