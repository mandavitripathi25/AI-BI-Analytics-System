"""Creates a messy sample_sales.csv to test the pipeline."""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
n = 3000
dates = pd.to_datetime("2023-01-01") + pd.to_timedelta(rng.integers(0, 730, n), unit="D")
qty = rng.integers(1, 10, n)
price = rng.choice([499, 999, 1499, 2499, 4999], n)
season = 1 + 0.3 * np.sin(2 * np.pi * dates.month / 12) + (dates - dates.min()).days / 2000

df = pd.DataFrame({
    " Order Date ": dates.strftime("%Y-%m-%d"),
    "Region": rng.choice(["North", "South", "East", "West"], n),
    "Category": rng.choice(["Electronics", "Fashion", "Home", "Sports"], n),
    "Quantity": qty,
    "Revenue": (qty * price * season).round(2),
})
df.loc[rng.choice(n, 60), "Region"] = None
df.loc[rng.choice(n, 40), "Revenue"] = None
df.loc[rng.choice(n, 10), "Revenue"] = 900000  # outliers
df = pd.concat([df, df.sample(50, random_state=1)])  # duplicates
df.to_csv("sample_sales.csv", index=False)
print("sample_sales.csv created")
