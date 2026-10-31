"""AI-Powered Business Intelligence & Data Analytics System  |  run: streamlit run app.py"""
import os

import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from ai_insights import ask_data, generate_insights, get_client
from cleaning import clean_data, load_file
from forecasting import forecast_series
from sql_analysis import detect_columns, run_query, standard_reports

load_dotenv()
st.set_page_config(page_title="AI BI System", page_icon="📊", layout="wide")
st.title("📊 AI-Powered Business Intelligence & Analytics")

# ---------- Sidebar ----------
api_key = st.sidebar.text_input("Groq API Key", type="password", value=os.getenv("GROQ_API_KEY", ""))
file = st.sidebar.file_uploader("Upload Excel / CSV", type=["csv", "xlsx", "xls"])
if not file:
    st.info("Upload a dataset from the sidebar to begin.")
    st.stop()

# ---------- Load + clean (once per file) ----------
key = (file.name, file.size)
if st.session_state.get("file_key") != key:
    raw = load_file(file)
    clean, report = clean_data(raw)
    st.session_state.update(file_key=key, raw=raw, df=clean, report=report, chat=[], insights=None)

raw, df, report = st.session_state.raw, st.session_state.df, st.session_state.report
date_col, value_col, cats = detect_columns(df)
numeric_cols = df.select_dtypes("number").columns.tolist()
date_cols = df.select_dtypes("datetime").columns.tolist()

tabs = st.tabs(["🧹 Data & Cleaning", "🗃️ SQL Analysis", "📈 Dashboard",
                "🔮 Forecast", "💡 AI Insights", "💬 Chat with Data"])

# ---------- 1. Data & cleaning ----------
with tabs[0]:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows before", report["rows_before"])
    c2.metric("Rows after", report["rows_after"])
    c3.metric("Missing filled", report["missing_before"])
    c4.metric("Outliers capped", report["outliers_capped"])
    st.caption(f"Duplicates removed: {report['duplicates_removed']}")
    st.subheader("Cleaned data")
    st.dataframe(df.head(100), use_container_width=True)
    st.download_button("⬇️ Download cleaned CSV (for Power BI)",
                       df.to_csv(index=False).encode("utf-8"), "cleaned_data.csv", "text/csv")

# ---------- 2. SQL ----------
with tabs[1]:
    if value_col is None:
        st.warning("No numeric column found.")
    else:
        cat_pick = st.selectbox("Group by", cats) if cats else None
        reports = standard_reports(df, date_col, value_col, cat_pick)
        st.session_state.reports = reports
        for name, table in reports.items():
            st.markdown(f"**{name}**")
            st.dataframe(table, use_container_width=True)
    st.subheader("Custom SQL (table name: `data`)")
    sql = st.text_area("Query", 'SELECT * FROM data LIMIT 10')
    if st.button("Run query"):
        try:
            st.dataframe(run_query(df, sql), use_container_width=True)
        except Exception as e:
            st.error(e)

# ---------- 3. Dashboard ----------
with tabs[2]:
    if value_col:
        k1, k2, k3 = st.columns(3)
        k1.metric(f"Total {value_col}", f"{df[value_col].sum():,.0f}")
        k2.metric(f"Average {value_col}", f"{df[value_col].mean():,.2f}")
        k3.metric("Records", f"{len(df):,}")
        left, right = st.columns(2)
        if date_col:
            m = df.set_index(date_col)[value_col].resample("MS").sum().reset_index()
            left.plotly_chart(px.line(m, x=date_col, y=value_col, title="Monthly trend", markers=True),
                              use_container_width=True)
        if cats:
            g = df.groupby(cats[0])[value_col].sum().nlargest(10).reset_index()
            right.plotly_chart(px.bar(g, x=cats[0], y=value_col, title=f"Top {cats[0]}"),
                               use_container_width=True)
            if len(cats) > 1:
                p = df.groupby(cats[1])[value_col].sum().reset_index()
                left.plotly_chart(px.pie(p, names=cats[1], values=value_col, title=f"Share by {cats[1]}"),
                                  use_container_width=True)
        right.plotly_chart(px.histogram(df, x=value_col, title=f"{value_col} distribution"),
                           use_container_width=True)

# ---------- 4. Forecast ----------
with tabs[3]:
    if not date_cols or not numeric_cols:
        st.warning("Need a date column and a numeric column to forecast.")
    else:
        f1, f2, f3 = st.columns(3)
        d = f1.selectbox("Date column", date_cols)
        v = f2.selectbox("Value column", numeric_cols,
                         index=numeric_cols.index(value_col) if value_col in numeric_cols else 0)
        n = f3.slider("Months to forecast", 3, 12, 6)
        try:
            hist, fc, metrics = forecast_series(df, d, v, n)
            fig = px.line(title=f"{v}: actual vs forecast")
            fig.add_scatter(x=hist["month"], y=hist["actual"], name="Actual", mode="lines+markers")
            fig.add_scatter(x=fc["month"], y=fc["forecast"], name="Forecast",
                            mode="lines+markers", line=dict(dash="dash"))
            st.plotly_chart(fig, use_container_width=True)
            if metrics:
                st.caption("Backtest on last 3 months: " + ", ".join(f"{k}: {x}" for k, x in metrics.items()))
            st.dataframe(fc, use_container_width=True)
        except Exception as e:
            st.error(e)

# ---------- 5. AI insights ----------
with tabs[4]:
    if not api_key:
        st.warning("Enter your Groq API key in the sidebar.")
    elif st.button("Generate AI insights"):
        with st.spinner("Analysing..."):
            reps = st.session_state.get("reports") or standard_reports(df, date_col, value_col, cats[0] if cats else None)
            st.session_state.insights = generate_insights(get_client(api_key), df, reps)
    if st.session_state.get("insights"):
        st.markdown(st.session_state.insights)

# ---------- 6. Chat ----------
with tabs[5]:
    if not api_key:
        st.warning("Enter your Groq API key in the sidebar.")
    else:
        for msg in st.session_state.chat:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("sql"):
                    with st.expander("SQL used"):
                        st.code(msg["sql"], language="sql")
        if q := st.chat_input("Ask anything, e.g. 'Which region had the highest revenue?'"):
            st.session_state.chat.append({"role": "user", "content": q})
            with st.spinner("Thinking..."):
                answer, sql, result = ask_data(get_client(api_key), df, q)
            st.session_state.chat.append({"role": "assistant", "content": answer, "sql": sql})
            st.rerun()
