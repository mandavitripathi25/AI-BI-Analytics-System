"""Feature 3: SQL-based analysis (SQLite in memory, table name = data)."""
import re
import sqlite3

import pandas as pd

FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|create|attach|pragma)\b", re.I)


def run_query(df: pd.DataFrame, sql: str, table: str = "data") -> pd.DataFrame:
    sql = sql.strip().rstrip(";")
    if not sql.lower().startswith(("select", "with")) or FORBIDDEN.search(sql):
        raise ValueError("Only read-only SELECT queries are allowed.")
    con = sqlite3.connect(":memory:")
    try:
        df.to_sql(table, con, index=False, if_exists="replace")
        return pd.read_sql_query(sql, con)
    finally:
        con.close()


def detect_columns(df: pd.DataFrame):
    """Guess the date column, the main value (revenue) column and category columns."""
    date_col = next((c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])), None)
    nums = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    keys = ("revenue", "sales", "amount", "total", "profit", "price")
    value_col = next((c for c in nums if any(k in c for k in keys)), nums[0] if nums else None)
    cats = [c for c in df.columns if df[c].dtype == "object" and 1 < df[c].nunique() <= 50]
    return date_col, value_col, cats


def standard_reports(df, date_col, value_col, cat_col):
    reports = {}
    reports["KPIs"] = run_query(df, f'''
        SELECT COUNT(*) AS rows_count,
               ROUND(SUM("{value_col}"), 2) AS total,
               ROUND(AVG("{value_col}"), 2) AS average,
               ROUND(MAX("{value_col}"), 2) AS max_value
        FROM data''')
    if cat_col:
        reports[f"Top {cat_col}"] = run_query(df, f'''
            SELECT "{cat_col}", ROUND(SUM("{value_col}"), 2) AS total,
                   COUNT(*) AS orders
            FROM data GROUP BY "{cat_col}" ORDER BY total DESC LIMIT 10''')
    if date_col:
        reports["Monthly trend"] = run_query(df, f'''
            SELECT strftime('%Y-%m', "{date_col}") AS month,
                   ROUND(SUM("{value_col}"), 2) AS total
            FROM data GROUP BY month ORDER BY month''')
    return reports
