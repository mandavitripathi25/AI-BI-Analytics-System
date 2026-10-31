"""Feature 1 & 2: load Excel/CSV and clean it automatically."""
import numpy as np
import pandas as pd


def load_file(file) -> pd.DataFrame:
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file)
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(file)
    raise ValueError("Please upload a .csv, .xlsx or .xls file")


def clean_data(df: pd.DataFrame):
    """Returns (clean_df, report_dict)."""
    df = df.copy()
    report = {"rows_before": len(df), "cols": df.shape[1]}

    # 1. Standardise column names -> snake_case
    df.columns = (
        df.columns.astype(str).str.strip().str.lower()
        .str.replace(r"[^0-9a-z]+", "_", regex=True).str.strip("_")
    )

    # 2. Drop empty rows/cols and exact duplicates
    df = df.dropna(how="all").dropna(axis=1, how="all")
    report["duplicates_removed"] = int(df.duplicated().sum())
    df = df.drop_duplicates()

    # 3. Trim text and turn blanks into NaN
    for c in df.select_dtypes(include="object").columns:
        df[c] = (
            df[c].astype(str).str.strip()
            .replace({"": np.nan, "nan": np.nan, "None": np.nan, "NA": np.nan, "N/A": np.nan})
        )

    # 4. Parse date columns
    for c in df.select_dtypes(include="object").columns:
        if "date" in c or "time" in c:
            df[c] = pd.to_datetime(df[c], errors="coerce")

    # 5. Convert numeric-looking text (e.g. "₹1,200") to numbers
    for c in df.select_dtypes(include="object").columns:
        converted = pd.to_numeric(df[c].str.replace(r"[₹$€,]", "", regex=True), errors="coerce")
        if converted.notna().mean() > 0.9:
            df[c] = converted

    # 6. Fill missing values
    report["missing_before"] = int(df.isna().sum().sum())
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            df[c] = df[c].fillna(df[c].median())
        elif pd.api.types.is_datetime64_any_dtype(df[c]):
            df[c] = df[c].ffill().bfill()
        else:
            mode = df[c].mode()
            df[c] = df[c].fillna(mode.iloc[0] if not mode.empty else "Unknown")

    # 7. Cap outliers with the IQR rule
    outliers = 0
    for c in df.select_dtypes(include="number").columns:
        q1, q3 = df[c].quantile([0.25, 0.75])
        iqr = q3 - q1
        if iqr == 0:
            continue
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers += int(((df[c] < lo) | (df[c] > hi)).sum())
        df[c] = df[c].clip(lo, hi)
    report["outliers_capped"] = outliers

    report["rows_after"] = len(df)
    return df.reset_index(drop=True), report
