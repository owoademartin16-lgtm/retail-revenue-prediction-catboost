# Retail Sales Intelligence

Daily sales analysis and forecasting for a retail business, from raw receipts to a live Streamlit dashboard.

## What it does

- Covers 125,751 receipts across 40 stores and 27 product categories (Jun 2025 to Apr 2026)
- Reports revenue, cost of goods, gross profit, margin, returns, and average receipt
- Breaks performance down by product, store, month, week, division, and sales type
- Ships a saved CatBoost model that turns recent daily sales into a next-day revenue estimate

## Dashboard pages

- **Overview** — headline KPIs, monthly revenue and gross profit, sales type mix, revenue-to-profit bridge, division split
- **Products** — top categories by revenue, category economics, margin and return signals
- **Stores** — top stores by revenue, profit and margin, store economics
- **Time** — weekly revenue rhythm, month spotlight, full monthly performance table
- **Returns** — returned revenue and lost profit by division and category
- **Forecast** — CatBoost next-day revenue estimate with demand bands

## Files

- `Business Sales.ipynb` — analysis, feature engineering, and model comparison
- `business_sales_app.py` — Streamlit dashboard entry point
- `charts.py` — Plotly chart builders
- `theme.py` — layout, styling, and formatting helpers
- `forecast.py` — model loading and feature construction
- `Business Sales.joblib` — trained CatBoost model and feature order
- `data/retail_sales_ml_apl.csv` — receipt-level dataset used by the dashboard
- `screenshots/` — full-page captures of every dashboard tab

## How to run

```bash
pip install -r requirements.txt
streamlit run business_sales_app.py
```
