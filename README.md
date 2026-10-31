# AI-Powered BI & Data Analytics System

## Run
```
pip install -r requirements.txt
cp .env.example .env        # add GROQ_API_KEY
python generate_sample_data.py   # optional test data
streamlit run app.py
```

## Power BI dashboard (Feature 4)
1. In the app, open **Data & Cleaning** and download `cleaned_data.csv`.
2. Power BI Desktop -> Get Data -> Text/CSV -> Load.
3. Make sure `order_date` is Date type. Create a Date table:
   `DateTable = CALENDAR(MIN(data[order_date]), MAX(data[order_date]))` and relate it to `order_date`.
4. DAX measures:
```
Total Revenue = SUM(data[revenue])
Total Orders = COUNTROWS(data)
Avg Order Value = DIVIDE([Total Revenue], [Total Orders])
Revenue LY = CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(DateTable[Date]))
YoY Growth % = DIVIDE([Total Revenue] - [Revenue LY], [Revenue LY])
```
5. Visuals: KPI cards, line chart (month vs revenue), bar (revenue by category), map/bar (region), slicers (date, region, category).
6. Optional: Home -> Publish to Power BI Service for sharing.

## Structure
- `cleaning.py` – load + auto clean
- `sql_analysis.py` – SQLite queries
- `forecasting.py` – trend + seasonality forecast
- `ai_insights.py` – Groq insights + text-to-SQL chat
- `app.py` – Streamlit UI
