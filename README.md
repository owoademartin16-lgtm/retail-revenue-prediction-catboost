# Retail Sales Forecast

Daily sales forecasting for a retail business, from raw receipts to a live prediction app.

## What it does

- Aggregates 125,751 transaction receipts into 326 daily sales totals
- Engineers calendar features plus lag (1, 7, 14, 30 days) and rolling-average features
- Compares Random Forest, Gradient Boosting, and CatBoost on the most recent 60 days
- Ships the winner (CatBoost, test R² 0.865, average miss $4,324/day) as a Streamlit app

## Files

- `Business Sales.ipynb` — analysis, feature engineering, and model comparison
- `business_sales_app.py` — Streamlit sales forecasting app
- `Business Sales.joblib` — trained CatBoost model and feature order

## How to run

```bash
pip install -r requirements.txt
streamlit run business_sales_app.py
```
