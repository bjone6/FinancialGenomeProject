
from pathlib import Path
import json
import calendar
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
WORKBOOK = ROOT / "data" / "NWLA Data.xlsx"
TEMPLATE = ROOT / "templates" / "unemployment_template.html"
OUTPUT = ROOT / "charts" / "unemployment.html"

# Row 4 contains the column headings
df = pd.read_excel(
    WORKBOOK,
    sheet_name="Unemployment",
    header=3
)

df.columns = df.columns.astype(str).str.strip()

required = [
    "Year",
    "Label",
    "Unemployment",
    "Unemployment Rate"
]

missing = [c for c in required if c not in df.columns]

if missing:
    raise ValueError(
        f"Missing columns: {missing}. "
        f"Found: {df.columns.tolist()}"
    )

# Convert Jan, Feb, Mar, etc. into month numbers
months = {
    calendar.month_abbr[i].lower(): i
    for i in range(1, 13)
}
months.update({
    calendar.month_name[i].lower(): i
    for i in range(1, 13)
})

def parse_month(value):
    if pd.isna(value):
        return None
    return months.get(str(value).strip().lower())

df["month"] = df["Label"].map(parse_month)
df["year"] = pd.to_numeric(
    df["Year"], errors="coerce"
)
df["count"] = pd.to_numeric(
    df["Unemployment"], errors="coerce"
)
df["rate"] = pd.to_numeric(
    df["Unemployment Rate"], errors="coerce"
)

df = df.dropna(
    subset=["year", "month", "count", "rate"]
).copy()

df["date"] = pd.to_datetime(
    dict(
        year=df["year"].astype(int),
        month=df["month"].astype(int),
        day=1
    )
)

df = (
    df.sort_values("date")
    .drop_duplicates(subset="date", keep="last")
)

if df.empty:
    raise ValueError("No valid monthly data found.")

# Prepare the monthly data for Plotly
records = [
    {
        "date": row.date.strftime("%Y-%m-%d"),
        "count": int(row.count),
        "rate": float(row.rate)
    }
    for row in df.itertuples(index=False)
]

# Insert the data into the original chart template
html = TEMPLATE.read_text(encoding="utf-8")

marker = "__RECORDS_JSON__"

if html.count(marker) != 1:
    raise ValueError(
        "Expected one data placeholder in template."
    )

html = html.replace(
    marker,
    json.dumps(records, separators=(",", ":"))
)

OUTPUT.parent.mkdir(
    parents=True, exist_ok=True
)

OUTPUT.write_text(
    html,
    encoding="utf-8"
)

print(
    f"Created {OUTPUT} with {len(records)} months, "
    f"through {df['date'].max():%B %Y}"
)
