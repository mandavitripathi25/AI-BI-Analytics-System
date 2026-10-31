"""Feature 5 & 7: AI insights + chat with your data (Groq, text-to-SQL)."""
import re

import pandas as pd
from groq import Groq

from sql_analysis import run_query

MODEL = MODEL = "openai/gpt-oss-120b"


def get_client(api_key: str) -> Groq:
    return Groq(api_key=api_key)


def _llm(client, system, user, temperature=0.2):
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=temperature,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return resp.choices[0].message.content.strip()


def schema_text(df: pd.DataFrame) -> str:
    lines = [f'- "{c}" ({t})' for c, t in df.dtypes.astype(str).items()]
    return "Table name: data\nColumns:\n" + "\n".join(lines)


def generate_insights(client, df, reports: dict) -> str:
    summary = "\n\n".join(f"### {k}\n{v.to_string(index=False)}" for k, v in reports.items())
    system = ("You are a senior business analyst. Give clear, specific, actionable insights. "
              "Use only the numbers provided; never invent data.")
    user = (f"{schema_text(df)}\n\nDataset has {len(df)} rows.\n\n"
            f"Analysis results:\n{summary}\n\n"
            "Write: 1) Key findings (5 bullets) 2) Risks/anomalies 3) Top 3 recommendations.")
    return _llm(client, system, user)


def _clean_sql(text: str) -> str:
    text = re.sub(r"```(?:sql)?", "", text, flags=re.I).replace("```", "").strip()
    return text


def ask_data(client, df, question: str):
    """Natural language -> SQL -> result -> plain-English answer."""
    sys_sql = ("You convert questions into a single SQLite SELECT query. "
               "Return ONLY the SQL, no explanation. Quote column names with double quotes.")
    base = f"{schema_text(df)}\n\nSample rows:\n{df.head(3).to_string(index=False)}\n\nQuestion: {question}"

    sql, result, error = "", None, None
    for attempt in range(2):  # retry once if the SQL fails
        prompt = base if error is None else f"{base}\n\nPrevious SQL failed: {sql}\nError: {error}\nFix it."
        sql = _clean_sql(_llm(client, sys_sql, prompt, temperature=0))
        try:
            result = run_query(df, sql)
            break
        except Exception as e:
            error = str(e)
    if result is None:
        return f"Sorry, I couldn't answer that. ({error})", sql, None

    answer = _llm(
        client,
        "You are a helpful data analyst. Answer briefly using only the query result.",
        f"Question: {question}\nSQL: {sql}\nResult:\n{result.head(30).to_string(index=False)}",
    )
    return answer, sql, result
