"""Plotly figures for the retail sales dashboard."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from theme import (
    AMBER,
    BLUE,
    BORDER,
    CORAL,
    DIVISION_COLORS,
    FAINT,
    GREEN,
    INK,
    MUTED,
    PINK,
    SALES_TYPE_COLORS,
    TEAL,
    VIOLET,
    VIOLET_SOFT,
    money,
)

DIVISION_SUFFIX = {
    "Scholar Footwear": "S",
    "Femme Footwear": "F",
    "Junior Apparel": "J",
}


def short_category(name: str) -> str:
    for division, suffix in DIVISION_SUFFIX.items():
        if name.startswith(division):
            rest = name[len(division) :].strip()
            return f"{rest} ({suffix})" if rest else division
    return name


def division_of(category: str) -> str:
    for division in DIVISION_COLORS:
        if category.startswith(division):
            return division
    return "Other"


def division_color(division: str) -> str:
    return DIVISION_COLORS.get(division, VIOLET_SOFT)


def style_figure(
    fig: go.Figure,
    height: int = 330,
    showlegend: bool = False,
    right_margin: int = 16,
) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=6, r=right_margin, t=10, b=6),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=MUTED, size=11),
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=BORDER, font=dict(color=INK, size=11)),
        showlegend=showlegend,
        legend=dict(orientation="h", y=1.12, x=0, font=dict(size=10)),
        hovermode="closest",
        bargap=0.28,
    )
    fig.update_xaxes(
        showgrid=False,
        gridcolor="#F1F3F8",
        zeroline=False,
        linecolor=BORDER,
        tickfont=dict(size=10, color=MUTED),
        title_font=dict(size=10, color=FAINT),
        automargin=True,
    )
    fig.update_yaxes(
        showgrid=False,
        gridcolor="#F1F3F8",
        zeroline=False,
        linecolor=BORDER,
        tickfont=dict(size=10, color=MUTED),
        title_font=dict(size=10, color=FAINT),
        automargin=True,
    )
    return fig


def monthly_revenue_chart(df: pd.DataFrame) -> go.Figure:
    m = (
        df.groupby("Month", observed=True)
        .agg(
            revenue=("Revenue", "sum"),
            profit=("Gross Profit", "sum"),
            receipts=("Is Return", "size"),
        )
        .reset_index()
        .sort_values("Month")
    )
    if m.empty:
        return blank_figure("No monthly data in this slice")

    q80 = float(m["revenue"].quantile(0.80))
    median = float(m["revenue"].median())
    colors = []
    for value in m["revenue"]:
        if value >= q80:
            colors.append(AMBER)
        elif value >= median:
            colors.append(VIOLET)
        else:
            colors.append(VIOLET_SOFT)

    custom = np.stack([m["profit"], m["receipts"]], axis=-1)
    fig = go.Figure()
    fig.add_bar(
        x=m["Month"],
        y=m["revenue"],
        name="Total revenue",
        marker_color=colors,
        marker_line_width=0,
        customdata=custom,
        hovertemplate=(
            "<b>%{x|%b %Y}</b><br>"
            "Total revenue %{y:$,.0f}<br>"
            "Gross profit %{customdata[0]:$,.0f}<br>"
            "%{customdata[1]:,.0f} receipts<extra></extra>"
        ),
    )
    fig.add_scatter(
        x=m["Month"],
        y=m["profit"],
        name="Gross profit",
        mode="lines+markers",
        line=dict(color=TEAL, width=2.4),
        marker=dict(size=5, color=TEAL, line=dict(color="#FFFFFF", width=1.4)),
        hovertemplate="<b>%{x|%b %Y}</b><br>Gross profit %{y:$,.0f}<extra></extra>",
    )
    fig.update_xaxes(
        tickformat="%b %y",
        dtick="M1" if len(m) <= 12 else "M2",
        tickangle=-35,
    )
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    return style_figure(fig, 342, showlegend=True)


def weekly_revenue_chart(df: pd.DataFrame) -> go.Figure:
    w = (
        df.set_index("Transaction Date")
        .resample("W-SUN")["Revenue"]
        .sum()
        .reset_index()
    )
    w = w[w["Revenue"] > 0]
    if w.empty:
        return blank_figure("No weekly data in this slice")

    fig = go.Figure(
        go.Scatter(
            x=w["Transaction Date"],
            y=w["Revenue"],
            mode="lines",
            line=dict(color=BLUE, width=2.2),
            fill="tozeroy",
            fillcolor="rgba(37,99,235,0.10)",
            hovertemplate="<b>Week ending %{x|%d %b %Y}</b><br>Total revenue %{y:$,.0f}<extra></extra>",
        )
    )
    peak = w.loc[w["Revenue"].idxmax()]
    fig.add_annotation(
        x=peak["Transaction Date"],
        y=peak["Revenue"],
        text=f"Peak {money(peak['Revenue'])}",
        showarrow=True,
        arrowhead=0,
        arrowwidth=1,
        arrowcolor=BLUE,
        ax=0,
        ay=-30,
        font=dict(size=10, color=BLUE, family="Space Mono"),
        bgcolor="#FFFFFF",
        bordercolor="#BFDBFE",
        borderwidth=1,
    )
    fig.update_xaxes(tickformat="%b %y")
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    return style_figure(fig, 320)


def category_revenue_chart(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    g = (
        df.groupby(["Product Category", "Product Division"], observed=True)["Revenue"]
        .sum()
        .reset_index()
        .nlargest(top_n, "Revenue")
        .sort_values("Revenue", ascending=True)
    )
    if g.empty:
        return blank_figure("No product data in this slice")

    labels = [short_category(c) for c in g["Product Category"]]
    colors = [division_color(d) for d in g["Product Division"]]
    text = [money(v) for v in g["Revenue"]]
    custom = np.stack([g["Product Category"], g["Product Division"]], axis=-1)
    fig = go.Figure(
        go.Bar(
            x=g["Revenue"],
            y=labels,
            orientation="h",
            marker_color=colors,
            marker_line_width=0,
            text=text,
            textposition="outside",
            cliponaxis=False,
            customdata=custom,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "%{customdata[1]}<br>"
                "Total revenue %{x:$,.0f}<extra></extra>"
            ),
        )
    )
    fig.update_xaxes(tickprefix="$", tickformat="~s")
    fig.update_yaxes(tickfont=dict(size=11, color=INK), showgrid=False)
    return style_figure(fig, 390, right_margin=64)


def profit_bridge_chart(df: pd.DataFrame) -> go.Figure:
    revenue = float(df["Revenue"].sum())
    cogs = float(df["COGS"].sum())
    profit = revenue - cogs
    fig = go.Figure(
        go.Waterfall(
            measure=["absolute", "relative", "total"],
            x=["Total revenue", "COGS", "Gross profit"],
            y=[revenue, -cogs, profit],
            text=[money(revenue), money(-cogs), money(profit)],
            textposition="outside",
            textfont=dict(size=11, color=INK, family="Space Mono"),
            connector=dict(line=dict(width=0)),
            increasing=dict(marker=dict(color=TEAL)),
            decreasing=dict(marker=dict(color=CORAL)),
            totals=dict(marker=dict(color=VIOLET)),
            hovertext=[
                f"<b>Total revenue</b><br>{money(revenue, compact=False)}",
                f"<b>COGS</b><br>{money(cogs, compact=False)}<br>Subtracted from revenue",
                f"<b>Gross profit</b><br>{money(profit, compact=False)}<br>{profit / revenue * 100:.2f}% margin",
            ],
            hoverinfo="text",
        )
    )
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    fig.update_xaxes(tickfont=dict(size=11, color=INK))
    return style_figure(fig, 320)


def sales_type_chart(df: pd.DataFrame) -> go.Figure:
    counts = df["Sales Type"].value_counts()
    order = [k for k in SALES_TYPE_COLORS if k in counts.index]
    order += [k for k in counts.index if k not in order]
    counts = counts.reindex(order)
    colors = [SALES_TYPE_COLORS.get(k, FAINT) for k in counts.index]
    fig = go.Figure(
        go.Pie(
            labels=counts.index,
            values=counts.values,
            hole=0.68,
            sort=False,
            direction="clockwise",
            marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
            textinfo="percent",
            textfont=dict(size=11, color="#FFFFFF", family="Inter"),
            hovertemplate="<b>%{label}</b><br>%{value:,.0f} receipts<br>%{percent}<extra></extra>",
        )
    )
    fig.add_annotation(
        text=f"<b>{len(df):,.0f}</b><br><span style='font-size:9px;color:{MUTED}'>receipts</span>",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(family="Space Grotesk", size=24, color=INK),
        align="center",
    )
    fig.update_layout(
        height=320,
        margin=dict(l=4, r=4, t=6, b=6),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center", font=dict(size=10)),
        font=dict(family="Inter, sans-serif", color=MUTED),
    )
    return fig


def division_chart(df: pd.DataFrame) -> go.Figure:
    g = df.groupby("Product Division", observed=True)["Revenue"].sum()
    order = [k for k in DIVISION_COLORS if k in g.index]
    order += [k for k in g.index if k not in order]
    g = g.reindex(order)
    colors = [division_color(k) for k in g.index]
    fig = go.Figure(
        go.Pie(
            labels=g.index,
            values=g.values,
            hole=0.68,
            sort=False,
            direction="clockwise",
            marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
            textinfo="percent",
            textfont=dict(size=11, color="#FFFFFF", family="Inter"),
            hovertemplate="<b>%{label}</b><br>Total revenue %{value:$,.0f}<br>%{percent}<extra></extra>",
        )
    )
    fig.add_annotation(
        text=f"<b>{money(g.sum())}</b><br><span style='font-size:9px;color:{MUTED}'>total revenue</span>",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(family="Space Grotesk", size=22, color=INK),
        align="center",
    )
    fig.update_layout(
        height=320,
        margin=dict(l=4, r=4, t=6, b=6),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(orientation="h", y=-0.10, x=0.5, xanchor="center", font=dict(size=9.5)),
        font=dict(family="Inter, sans-serif", color=MUTED),
    )
    return fig


def store_chart(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    g = (
        df.groupby("Store", observed=True)
        .agg(
            revenue=("Revenue", "sum"),
            profit=("Gross Profit", "sum"),
            receipts=("Is Return", "size"),
        )
        .reset_index()
        .nlargest(top_n, "revenue")
        .sort_values("revenue", ascending=True)
    )
    if g.empty:
        return blank_figure("No store data in this slice")

    colors = []
    for i in range(len(g)):
        if i == len(g) - 1:
            colors.append(AMBER)
        elif i == len(g) - 2:
            colors.append(CORAL)
        else:
            colors.append(VIOLET_SOFT)
    margin = np.where(g["revenue"] > 0, g["profit"] / g["revenue"] * 100, 0.0)
    custom = np.stack([g["profit"], margin, g["receipts"]], axis=-1)
    fig = go.Figure(
        go.Bar(
            x=g["revenue"],
            y=g["Store"],
            orientation="h",
            marker_color=colors,
            marker_line_width=0,
            text=[money(v) for v in g["revenue"]],
            textposition="outside",
            cliponaxis=False,
            customdata=custom,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Total revenue %{x:$,.0f}<br>"
                "Gross profit %{customdata[0]:$,.0f}<br>"
                "Margin %{customdata[1]:.2f}%<br>"
                "%{customdata[2]:,.0f} receipts<extra></extra>"
            ),
        )
    )
    fig.update_xaxes(tickprefix="$", tickformat="~s")
    fig.update_yaxes(tickfont=dict(size=11, color=INK), showgrid=False)
    return style_figure(fig, 390, right_margin=64)


def return_division_chart(df: pd.DataFrame) -> go.Figure:
    returns = df[df["Is Return"] == 1]
    if returns.empty:
        return blank_figure("No returned records in this slice")
    g = (
        returns.groupby("Product Division", observed=True)
        .agg(
            returned=("Sales Amount", lambda values: abs(values.sum())),
            lost_profit=("Gross Profit", lambda values: abs(values.sum())),
        )
        .reset_index()
        .sort_values("returned", ascending=True)
    )
    fig = go.Figure()
    fig.add_bar(
        y=g["Product Division"],
        x=g["returned"],
        name="Returned revenue",
        orientation="h",
        marker_color=CORAL,
        marker_line_width=0,
        text=[money(v) for v in g["returned"]],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Returned revenue %{x:$,.0f}<extra></extra>",
    )
    fig.add_bar(
        y=g["Product Division"],
        x=g["lost_profit"],
        name="Lost profit",
        orientation="h",
        marker_color=AMBER,
        marker_line_width=0,
        text=[money(v) for v in g["lost_profit"]],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Lost profit %{x:$,.0f}<extra></extra>",
    )
    fig.update_layout(barmode="group", showlegend=True)
    fig.update_xaxes(tickprefix="$", tickformat="~s")
    fig.update_yaxes(tickfont=dict(size=11, color=INK), showgrid=False)
    return style_figure(fig, 400, showlegend=True, right_margin=64)


def return_category_chart(df: pd.DataFrame, top_n: int = 8) -> go.Figure:
    returns = df[df["Is Return"] == 1]
    if returns.empty:
        return blank_figure("No returned records in this slice")
    g = (
        returns.groupby(["Product Category", "Product Division"], observed=True)
        .agg(returned=("Sales Amount", lambda values: abs(values.sum())))
        .reset_index()
        .nlargest(top_n, "returned")
        .sort_values("returned", ascending=True)
    )
    labels = [short_category(c) for c in g["Product Category"]]
    colors = [division_color(d) for d in g["Product Division"]]
    fig = go.Figure(
        go.Bar(
            x=g["returned"],
            y=labels,
            orientation="h",
            marker_color=colors,
            marker_line_width=0,
            text=[money(v) for v in g["returned"]],
            textposition="outside",
            cliponaxis=False,
            customdata=np.stack([g["Product Category"], g["Product Division"]], axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "%{customdata[1]}<br>"
                "Returned revenue %{x:$,.0f}<extra></extra>"
            ),
        )
    )
    fig.update_xaxes(tickprefix="$", tickformat="~s")
    fig.update_yaxes(tickfont=dict(size=11, color=INK), showgrid=False)
    return style_figure(fig, 400, right_margin=64)


def month_spotlight_chart(df: pd.DataFrame, month: pd.Timestamp) -> go.Figure:
    d = df[df["Month"] == month]
    if d.empty:
        return blank_figure("No records in the selected month")
    g = (
        d.groupby(["Product Category", "Product Division"], observed=True)["Revenue"]
        .sum()
        .reset_index()
        .nlargest(10, "Revenue")
        .sort_values("Revenue", ascending=True)
    )
    labels = [short_category(c) for c in g["Product Category"]]
    colors = [division_color(d) for d in g["Product Division"]]
    fig = go.Figure(
        go.Bar(
            x=g["Revenue"],
            y=labels,
            orientation="h",
            marker_color=colors,
            marker_line_width=0,
            text=[money(v) for v in g["Revenue"]],
            textposition="outside",
            cliponaxis=False,
            customdata=np.stack([g["Product Category"], g["Product Division"]], axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "%{customdata[1]}<br>"
                "Total revenue %{x:$,.0f}<extra></extra>"
            ),
        )
    )
    fig.update_xaxes(tickprefix="$", tickformat="~s")
    fig.update_yaxes(tickfont=dict(size=11, color=INK), showgrid=False)
    return style_figure(fig, 350, right_margin=64)


def model_comparison_chart() -> go.Figure:
    models = ["Gradient Boosting", "Random Forest", "Tuned CatBoost", "CatBoost"]
    r2 = [0.7399, 0.7668, 0.8192, 0.8652]
    mae = [5542.76, 5996.40, 5310.03, 4324.04]
    colors = [TEAL, BLUE, VIOLET_SOFT, VIOLET]

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Test R²", "Average miss (MAE)"),
        horizontal_spacing=0.18,
    )
    fig.add_trace(
        go.Bar(
            x=r2,
            y=models,
            orientation="h",
            marker_color=colors,
            marker_line_width=0,
            text=[f"{v:.3f}" for v in r2],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>R² %{x:.4f}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=mae,
            y=models,
            orientation="h",
            marker_color=colors,
            marker_line_width=0,
            text=[money(v) for v in mae],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>MAE %{x:$,.0f}<extra></extra>",
        ),
        row=1,
        col=2,
    )
    fig.update_xaxes(range=[0.60, 1.00], tickformat=".2f", showgrid=True, gridcolor="#F1F3F8", row=1, col=1)
    fig.update_xaxes(range=[0, 7200], tickprefix="$", tickformat=",.0f", showgrid=True, gridcolor="#F1F3F8", row=1, col=2)
    fig.update_yaxes(showgrid=False, tickfont=dict(size=10.5, color=INK))
    fig.update_layout(
        height=340,
        margin=dict(l=6, r=20, t=34, b=6),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        bargap=0.36,
        font=dict(family="Inter, sans-serif", color=MUTED, size=11),
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=BORDER, font=dict(color=INK, size=11)),
    )
    for annotation in fig.layout.annotations:
        annotation.font = dict(size=11, color=MUTED, family="Space Mono")
    return fig


def blank_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=12, color=FAINT, family="Inter"),
    )
    fig.update_layout(
        height=260,
        margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig
