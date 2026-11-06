"""Visual system for the retail sales dashboard."""
from __future__ import annotations

import textwrap

import streamlit as st

INK = "#121826"
MUTED = "#667085"
FAINT = "#98A2B3"
BORDER = "#E4E7EC"
SURFACE = "#FFFFFF"
SURFACE_ALT = "#F8FAFC"

VIOLET = "#6D28D9"
VIOLET_SOFT = "#A78BFA"
CORAL = "#F43F5E"
TEAL = "#0D9488"
AMBER = "#F59E0B"
BLUE = "#2563EB"
GREEN = "#16A34A"
PINK = "#DB2777"
ORANGE = "#FB7185"

DIVISION_COLORS = {
    "Scholar Footwear": VIOLET,
    "Femme Footwear": CORAL,
    "Junior Apparel": TEAL,
}

SALES_TYPE_COLORS = {
    "Full Price": VIOLET,
    "Promo": AMBER,
    "Markdown Tier 1": BLUE,
    "Markdown Tier 2": PINK,
    "Clearance": CORAL,
}

CHANNEL_COLORS = {
    "Online": BLUE,
    "Channel Alpha": VIOLET,
    "Channel Beta": TEAL,
    "Channel Gamma": AMBER,
    "Channel Delta": CORAL,
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
  --ink: #121826;
  --muted: #667085;
  --faint: #98A2B3;
  --border: #E4E7EC;
  --surface: #FFFFFF;
  --surface-alt: #F8FAFC;
  --violet: #6D28D9;
  --violet-soft: #A78BFA;
  --coral: #F43F5E;
  --teal: #0D9488;
  --amber: #F59E0B;
  --blue: #2563EB;
}

html, body, .stApp {
  background: #FFFFFF;
  color: var(--ink);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp { background: #FFFFFF; }
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { visibility: visible; }
[data-testid="stAppDeployButton"],
[data-testid="stMainMenu"] { display: none !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stExpandSidebarButton"] {
  visibility: visible !important;
  background: #FFFFFF !important;
  border: 1px solid #E4E7EC !important;
  border-radius: 10px !important;
  box-shadow: 0 6px 18px rgba(16, 24, 40, 0.10);
}
[data-testid="stExpandSidebarButton"]:hover { background: #F8FAFC !important; }
[data-testid="stSidebarCollapseButton"] button {
  visibility: visible !important;
  background: #FFFFFF !important;
  border: 1px solid #E4E7EC !important;
  border-radius: 10px !important;
}

[data-testid="stMainBlockContainer"] {
  max-width: 1480px;
  padding-top: 82px;
  padding-bottom: 3rem;
}

/* ---------------------------------------------------------------- sidebar */
section[data-testid="stSidebar"] {
  background: #FBFBFD;
  border-right: 1px solid var(--border);
}
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 2px 0 17px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 15px;
}
.sidebar-mark {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--violet), var(--coral));
  color: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 18px;
  font-weight: 700;
  box-shadow: 0 10px 20px -12px rgba(109, 40, 217, 0.65);
}
.sidebar-name {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 15px;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -0.02em;
  line-height: 1.2;
}
.sidebar-sub {
  font-family: 'Space Mono', monospace;
  font-size: 9px;
  color: var(--muted);
  letter-spacing: 0.10em;
  text-transform: uppercase;
  margin-top: 2px;
}
.sidebar-heading {
  font-family: 'Space Mono', monospace;
  font-size: 9.5px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--violet);
  margin: 17px 0 6px;
}
.sidebar-note {
  font-size: 10.5px;
  color: var(--faint);
  line-height: 1.55;
  margin-top: 4px;
}
.sidebar-snapshot {
  border: 1px solid #E9ECF3;
  border-radius: 12px;
  background: #FFFFFF;
  padding: 11px 12px;
  margin-top: 14px;
}
.sidebar-snapshot .k {
  font-family: 'Space Mono', monospace;
  font-size: 8.5px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--faint);
}
.sidebar-snapshot .v {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 17px;
  font-weight: 700;
  color: var(--ink);
  margin-top: 1px;
}
section[data-testid="stSidebar"] > div { padding-top: 1.4rem; }
section[data-testid="stSidebar"] label[data-testid="stWidgetLabel"] p {
  color: var(--muted);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
section[data-testid="stSidebar"] div[data-baseweb="input"] > div,
section[data-testid="stSidebar"] div[data-baseweb="base-input"] {
  background: #FFFFFF !important;
  border-color: var(--border) !important;
  border-radius: 10px !important;
}
[data-testid="stMultiSelect"] [data-tag] {
  background: #F3EEFF !important;
  color: #5B21B6 !important;
  border: 1px solid #DDD6FE !important;
  border-radius: 8px !important;
  font-size: 11.5px !important;
}
[data-testid="stMultiSelect"] [data-tag] span { color: #5B21B6 !important; }
[data-testid="stMultiSelect"] [data-tag] button { color: #7C3AED !important; }
section[data-testid="stSidebar"] .stButton > button {
  border-radius: 12px;
  font-weight: 700;
}
div.stButton > button[kind="primary"] {
  background: linear-gradient(90deg, #6D28D9, #A78BFA);
  border: none;
  color: #FFFFFF !important;
  border-radius: 12px;
  font-weight: 700;
  box-shadow: 0 8px 20px -10px rgba(109, 40, 217, 0.55);
}
div.stButton > button[kind="primary"]:hover { filter: brightness(1.06); }
div.stButton > button[kind="secondary"] {
  background: #FFFFFF;
  border: 1px solid var(--border);
  color: #344054;
  border-radius: 12px;
  font-weight: 600;
}
div.stButton > button[kind="secondary"]:hover {
  border-color: var(--violet);
  color: var(--violet);
}

/* ---------------------------------------------------------------- hero */
.hero {
  position: relative;
  overflow: hidden;
  border: 1px solid #E9E4FF;
  border-radius: 26px;
  padding: 14px 34px 28px;
  background:
    radial-gradient(560px 220px at 92% 4%, rgba(167, 139, 250, 0.20), transparent 62%),
    radial-gradient(420px 220px at 6% 100%, rgba(244, 63, 94, 0.10), transparent 60%),
    linear-gradient(135deg, #FFFFFF 0%, #FAF7FF 58%, #FFF7F4 100%);
  box-shadow: 0 24px 60px -42px rgba(70, 35, 140, 0.45);
  margin-bottom: 18px;
}
.hero::after {
  content: "";
  position: absolute;
  width: 220px;
  height: 220px;
  right: -80px;
  top: -110px;
  border-radius: 50%;
  border: 26px solid rgba(109, 40, 217, 0.08);
}
.hero-kicker {
  font-family: 'Space Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--violet);
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 12px;
}
.hero-kicker::before {
  content: "";
  width: 24px;
  height: 2px;
  border-radius: 2px;
  background: linear-gradient(90deg, var(--violet), var(--coral));
}
.hero h1 {
  font-family: 'Space Grotesk', sans-serif !important;
  color: var(--ink) !important;
  font-size: clamp(2rem, 4vw, 3rem) !important;
  font-weight: 700 !important;
  letter-spacing: -0.035em !important;
  line-height: 1.06 !important;
  margin: 0 0 10px !important;
}
.hero p {
  color: var(--muted) !important;
  font-size: 15px !important;
  line-height: 1.65 !important;
  max-width: 74ch;
  margin: 0 !important;
}
.hero-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }
.hero-tag {
  font-family: 'Space Mono', monospace;
  font-size: 10px;
  color: #475467;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid #E7E2F5;
  border-radius: 999px;
  padding: 6px 11px;
}
.hero-tag b { color: var(--violet); }

/* ---------------------------------------------------------------- KPI cards */
.kpi-card {
  position: relative;
  overflow: hidden;
  background: #FFFFFF;
  border: 1px solid #E9ECF3;
  border-radius: 14px;
  padding: 15px 16px 14px 18px;
  min-height: 104px;
  box-shadow: 0 14px 34px -30px rgba(16, 24, 40, 0.45);
  margin-bottom: 8px;
}
.kpi-card::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 4px;
  background: var(--accent);
}
.kpi-label {
  font-family: 'Space Mono', monospace;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent);
}
.kpi-value {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.7rem;
  font-weight: 700;
  letter-spacing: -0.035em;
  line-height: 1.1;
  color: var(--ink);
  margin-top: 10px;
}
.kpi-sub {
  font-size: 11px;
  color: var(--muted);
  margin-top: 3px;
  line-height: 1.4;
}

/* ---------------------------------------------------------------- cards and text */
div[data-testid="stLayoutWrapper"] > div[data-testid="stVerticalBlock"]:has([data-testid="stPlotlyChart"]),
div[data-testid="stLayoutWrapper"] > div[data-testid="stVerticalBlock"]:has([data-testid="stDataFrame"]),
div[data-testid="stLayoutWrapper"] > div[data-testid="stVerticalBlock"]:has(.mini-stat),
div[data-testid="stLayoutWrapper"] > div[data-testid="stVerticalBlock"]:has([data-testid="stSelectbox"]) {
  background: #FFFFFF;
  border: 1px solid #E9ECF3 !important;
  border-radius: 18px !important;
  padding: 1rem 1.15rem 0.9rem !important;
  box-shadow: 0 16px 40px -36px rgba(16, 24, 40, 0.42);
}
div[data-testid="stVerticalBlock"]:has(.stores-layout) div[data-testid="stLayoutWrapper"] > div[data-testid="stVerticalBlock"]:has([data-testid="stPlotlyChart"]),
div[data-testid="stVerticalBlock"]:has(.stores-layout) div[data-testid="stLayoutWrapper"] > div[data-testid="stVerticalBlock"]:has(.mini-stat) {
  min-height: 469px;
}
.chart-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 15px;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -0.01em;
}
.chart-sub {
  font-size: 11.5px;
  color: var(--muted);
  margin-top: 2px;
  margin-bottom: 4px;
  line-height: 1.45;
}
.section-kicker {
  font-family: 'Space Mono', monospace;
  font-size: 9.5px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--violet);
}
.section-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 20px;
  font-weight: 700;
  color: var(--ink);
  margin: 2px 0 4px;
  letter-spacing: -0.02em;
}
.section-text { color: var(--muted); font-size: 12.5px; line-height: 1.6; }
.insight {
  background: linear-gradient(90deg, #F8F4FF 0%, #FFF7F5 100%);
  border: 1px solid #ECE6FB;
  border-left: 4px solid var(--violet);
  border-radius: 14px;
  padding: 13px 16px;
  color: #475467;
  font-size: 12.5px;
  line-height: 1.6;
  margin: 8px 0 4px;
}
.insight strong { color: var(--ink); }
.mini-pill {
  display: inline-block;
  font-family: 'Space Mono', monospace;
  font-size: 9px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--violet);
  background: #F3EEFF;
  border: 1px solid #DDD6FE;
  border-radius: 999px;
  padding: 2px 8px;
  margin-left: 6px;
}
.mini-stat {
  background: #FFFFFF;
  border: 1px solid #E9ECF3;
  border-radius: 14px;
  padding: 12px 14px;
  margin-bottom: 8px;
}
.mini-stat .label {
  font-family: 'Space Mono', monospace;
  font-size: 9px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}
.mini-stat .value {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 22px;
  font-weight: 700;
  color: var(--ink);
  margin-top: 3px;
}
.mini-stat .sub { font-size: 10.5px; color: var(--muted); }

/* ---------------------------------------------------------------- tabs */
.stTabs [role="tablist"] {
  gap: 6px;
  background: #F4F5F9;
  border-radius: 14px;
  padding: 6px;
  margin-bottom: 12px;
}
.stTabs [data-testid="stTab"] {
  border-radius: 10px;
  padding: 8px 16px;
  font-family: 'Inter', sans-serif;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--muted);
  background: transparent;
}
.stTabs [data-testid="stTab"][aria-selected="true"] {
  background: #FFFFFF;
  color: var(--violet);
  box-shadow: 0 3px 10px rgba(16, 24, 40, 0.08);
}

/* ---------------------------------------------------------------- tables and data */
div[data-testid="stDataFrame"] {
  border: 1px solid #E9ECF3;
  border-radius: 14px;
  overflow: hidden;
}
[data-testid="stExpander"] {
  border: 1px solid #E9ECF3;
  border-radius: 14px;
  background: #FFFFFF;
}

/* ---------------------------------------------------------------- forecast */
.forecast-card {
  position: relative;
  overflow: hidden;
  border-radius: 20px;
  padding: 24px 26px;
  color: #FFFFFF;
  background: linear-gradient(135deg, #4C1D95 0%, #7C3AED 58%, #A78BFA 100%);
  box-shadow: 0 26px 60px -34px rgba(76, 29, 149, 0.75);
}
.forecast-card.quiet { background: linear-gradient(135deg, #1E3A8A, #60A5FA); }
.forecast-card.steady { background: linear-gradient(135deg, #4C1D95, #A78BFA); }
.forecast-card.peak { background: linear-gradient(135deg, #92400E, #F59E0B); }
.forecast-label {
  font-family: 'Space Mono', monospace;
  font-size: 9.5px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.78);
}
.forecast-value {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 2.6rem;
  font-weight: 700;
  letter-spacing: -0.04em;
  margin: 6px 0 2px;
}
.forecast-date { font-size: 12px; color: rgba(255, 255, 255, 0.82); }
.forecast-band {
  display: inline-block;
  margin-top: 12px;
  background: rgba(255, 255, 255, 0.20);
  border: 1px solid rgba(255, 255, 255, 0.28);
  border-radius: 999px;
  padding: 5px 12px;
  font-size: 11px;
  font-weight: 700;
}
.forecast-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  font-family: 'Space Mono', monospace;
  font-size: 10.5px;
  color: var(--muted);
  letter-spacing: 0.01em;
}
.forecast-meta strong { color: var(--ink); font-weight: 700; }
.forecast-meta-sep { color: #C4C9D4; }
.band-panel {
  border: 1px solid #E9ECF3;
  border-radius: 18px;
  background: #FFFFFF;
  padding: 18px 20px 16px;
  margin-top: 14px;
  box-shadow: 0 16px 40px -36px rgba(16, 24, 40, 0.42);
}
.band-panel-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 15px;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -0.02em;
}
.band-panel-sub {
  font-family: 'Space Mono', monospace;
  font-size: 9px;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  color: var(--faint);
  margin-top: 3px;
}
.band-list { display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }
.band-row {
  display: grid;
  grid-template-columns: 9px 92px 150px minmax(0, 1fr);
  gap: 10px;
  align-items: center;
  border: 1px solid #EEF0F5;
  border-radius: 12px;
  background: #FBFBFD;
  padding: 10px 12px;
}
.band-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #CBD5E1;
}
.band-row.quiet .band-dot { background: var(--blue); }
.band-row.steady .band-dot { background: var(--violet); }
.band-row.peak .band-dot { background: var(--amber); }
.band-name {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 12px;
  font-weight: 700;
  color: var(--ink);
}
.band-range {
  font-family: 'Space Mono', monospace;
  font-size: 9.5px;
  color: var(--muted);
  white-space: nowrap;
}
.band-action { font-size: 11.5px; color: var(--muted); line-height: 1.45; }
.band-row.quiet.active { background: #EFF6FF; border-color: #BFDBFE; }
.band-row.steady.active { background: #F5F3FF; border-color: #DDD6FE; }
.band-row.peak.active { background: #FFFBEB; border-color: #FDE68A; }
.band-row.quiet.active .band-name { color: #1E3A8A; }
.band-row.steady.active .band-name { color: #4C1D95; }
.band-row.peak.active .band-name { color: #92400E; }
.band-panel-note {
  margin-top: 10px;
  font-size: 10.5px;
  color: var(--faint);
}
.demand-callout {
  border-radius: 14px;
  padding: 13px 16px;
  margin-top: 12px;
  font-size: 12px;
  line-height: 1.5;
  font-weight: 600;
  border: 1px solid #E9ECF3;
  background: #F8FAFC;
  color: var(--ink);
}
.demand-callout.quiet { background: #EFF6FF; border-color: #BFDBFE; color: #1E3A8A; }
.demand-callout.steady { background: #F5F3FF; border-color: #DDD6FE; color: #4C1D95; }
.demand-callout.peak { background: #FFFBEB; border-color: #FDE68A; color: #92400E; }

/* ---------------------------------------------------------------- footer */

@media (max-width: 1100px) {
  div[data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
  div[data-testid="stColumn"] { flex: 1 1 280px !important; min-width: 280px !important; }
}

@media (max-width: 900px) {
  .hero { padding: 22px 20px; border-radius: 20px; }
  .hero h1 { font-size: 2rem !important; }
  .stTabs [role="tablist"] { gap: 4px; padding: 5px; }
  .stTabs [data-testid="stTab"] { padding: 7px 10px; font-size: 11.5px; }
  .band-row { grid-template-columns: 9px 1fr; }
  .band-row .band-range,
  .band-row .band-action { grid-column: 2; }
  .band-row .band-range { margin-top: 2px; }
  div[data-testid="stLayoutWrapper"] > div[data-testid="stVerticalBlock"]:has([data-testid="stPlotlyChart"]),
  div[data-testid="stLayoutWrapper"] > div[data-testid="stVerticalBlock"]:has([data-testid="stDataFrame"]),
  div[data-testid="stLayoutWrapper"] > div[data-testid="stVerticalBlock"]:has(.mini-stat),
  div[data-testid="stLayoutWrapper"] > div[data-testid="stVerticalBlock"]:has([data-testid="stSelectbox"]) {
    padding: 0.8rem 0.8rem 0.7rem !important;
  }
}
</style>
"""


def md(html_text: str) -> None:
    st.markdown(textwrap.dedent(html_text).strip(), unsafe_allow_html=True)


def money(value: float, compact: bool = True, decimals: int = 2) -> str:
    sign = "-" if value < 0 else ""
    v = abs(float(value))
    if compact and v >= 1_000_000:
        return f"{sign}${v / 1_000_000:,.{decimals}f}M"
    if compact and v >= 1_000:
        return f"{sign}${v / 1_000:,.1f}K"
    return f"{sign}${v:,.{decimals}f}"


def number(value: float) -> str:
    return f"{value:,.0f}"


def percent(value: float, decimals: int = 2) -> str:
    return f"{value:,.{decimals}f}%"


def kpi_card(label: str, value: str, sub: str, accent: str) -> str:
    return f"""
    <div class="kpi-card" style="--accent:{accent}">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-sub">{sub}</div>
    </div>
    """


def section(kicker: str, title: str, text: str) -> None:
    md(f"""
    <div style="margin:6px 0 10px">
      <div class="section-kicker">{kicker}</div>
      <div class="section-title">{title}</div>
      <div class="section-text">{text}</div>
    </div>
    """)


def chart_header(title: str, subtitle: str) -> None:
    md(f'<div class="chart-title">{title}</div><div class="chart-sub">{subtitle}</div>')
