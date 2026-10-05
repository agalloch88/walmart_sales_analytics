"""Build docs/index.html: one chart per required report, modeled on the reference reports
in the requirements doc. Reads the reporting views in Snowflake through db.query_df."""
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from db import query_df

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "index.html"

# Validated categorical colors: 2-3 series use the first three; the 5 markdowns use all five.
BLUE, ORANGE, VIOLET = "#2a78d6", "#eb6834", "#4a3aa7"
THREE = [BLUE, ORANGE, VIOLET]
FIVE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
TYPES = ["A", "B", "C"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load(sql_file: str) -> pd.DataFrame:
    df = query_df((HERE / "queries" / sql_file).read_text())
    if df.empty:
        raise RuntimeError(f"{sql_file} returned no rows")
    for col in df.columns:  # Decimal values make Plotly draw blank or sideways bars
        if df[col].dtype == object and df[col].map(lambda v: isinstance(v, Decimal)).any():
            raise RuntimeError(f"{sql_file}: column {col} holds Decimal values; "
                               "use the db.py that converts them to floats")
    return df


def money(v) -> str:
    if pd.isna(v):
        return ""
    v = float(v)
    for size, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(v) >= size:
            return f"${v / size:.2f}{suffix}" if suffix == "B" else f"${v / size:.0f}{suffix}"
    return f"${v:,.0f}"


def is_holiday(s: pd.Series) -> pd.Series:
    """Accept Y/N, TRUE/FALSE or real booleans, whatever the date dim produced."""
    return s.astype(str).str.strip().str.upper().isin(["Y", "TRUE", "T", "1"])


def style(fig, height=480, money_axis="y"):
    fig.update_layout(
        template="plotly_white",
        height=height,
        font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", size=13, color="#1f1f1f"),
        margin=dict(t=50, r=24, b=50, l=70),
        legend=dict(orientation="h", x=0, y=1.02, yanchor="bottom", title_text=""),
        barcornerradius=4,
        bargap=0.25,
        hoverlabel=dict(font_size=12),
    )
    fig.update_xaxes(gridcolor="#ececec", linecolor="#c9c9c9")
    fig.update_yaxes(gridcolor="#ececec", zerolinecolor="#c9c9c9")
    if money_axis == "y":
        fig.update_yaxes(tickprefix="$")
    elif money_axis == "x":
        fig.update_xaxes(tickprefix="$", col=2)
    return fig


# 1. Weekly sales by store and holiday
def sales_by_store_holiday():
    df = load("01_sales_by_store_holiday.sql")
    df["week_type"] = np.where(is_holiday(df["isholiday"]), "Holiday weeks", "Other weeks")
    fig = px.bar(
        df, x="store_id", y="total_sales", color="week_type", barmode="group", orientation="v",
        category_orders={"week_type": ["Other weeks", "Holiday weeks"]},
        color_discrete_sequence=[BLUE, ORANGE],
        labels={"store_id": "Store", "total_sales": "Total sales ($)"},
    )
    fig.update_traces(hovertemplate="Store %{x}<br>%{fullData.name}: %{y:$,.0f}<extra></extra>")
    fig.update_xaxes(dtick=5)
    return style(fig)


# 2. Weekly sales by temperature and year
def sales_by_temperature_year():
    df = load("02_sales_by_temperature_year.sql")
    df["band_key"] = df["temp_band"].astype(float).clip(lower=0, upper=100).astype(int)
    df["band"] = df["band_key"].map(
        lambda b: "Below 10°F" if b < 10 else "100°F+" if b >= 100 else f"{b}–{b + 9}°F")
    df["sales_year"] = df["sales_year"].astype(int).astype(str)
    agg = df.groupby(["sales_year", "band_key", "band"], as_index=False)["total_sales"].sum()
    band_order = agg.sort_values("band_key")["band"].unique().tolist()
    fig = px.bar(
        agg, x="band", y="total_sales", color="sales_year", barmode="group", orientation="v",
        category_orders={"band": band_order, "sales_year": sorted(agg["sales_year"].unique())},
        color_discrete_sequence=THREE,
        labels={"band": "Store-week temperature", "total_sales": "Total sales ($)"},
    )
    fig.update_traces(hovertemplate="%{x}, %{fullData.name}<br>%{y:$,.0f}<extra></extra>")
    return style(fig)


# 3. Weekly sales by store size
def sales_by_store_size():
    df = load("03_sales_by_store_size.sql").sort_values("store_size")
    fig = px.area(
        df, x="store_size", y="total_sales", markers=True,
        custom_data=["store_id", "store_type"], color_discrete_sequence=[BLUE],
        labels={"store_size": "Store size (sq ft)", "total_sales": "Total sales ($)"},
    )
    fig.update_traces(
        line_width=2, marker_size=8,
        hovertemplate="Store %{customdata[0]} (type %{customdata[1]})<br>"
                      "%{x:,} sq ft<br>%{y:$,.0f}<extra></extra>",
    )
    return style(fig)


# 4. Weekly sales by store type and month
def sales_by_type_month():
    df = load("04_sales_by_type_month.sql")
    df["month"] = df["sales_month"].astype(int).map(lambda m: MONTHS[m - 1])
    fig = px.line(
        df, x="month", y="total_sales", color="store_type", markers=True,
        category_orders={"month": MONTHS, "store_type": TYPES},
        color_discrete_sequence=THREE,
        labels={"month": "Month", "total_sales": "Total sales ($)", "store_type": "Store type"},
    )
    fig.update_traces(line_width=2, marker_size=8,
                      hovertemplate="Type %{fullData.name}: %{y:$,.0f}<extra></extra>")
    fig.for_each_trace(lambda t: t.update(name=f"Type {t.name}"))
    for trace in fig.data:  # direct label at each line's December point
        fig.add_annotation(x=trace.x[-1], y=trace.y[-1], text=trace.name, showarrow=False,
                           xanchor="left", xshift=8, font=dict(color="#1f1f1f", size=12))
    fig.update_layout(hovermode="x unified")
    return style(fig)


# 5. Markdown sales by year and store (dropdown picks all stores or one store)
def markdowns_by_year_store():
    df = load("05_markdowns_by_year_store.sql")
    md = [f"markdown{i}" for i in range(1, 6)]
    df["sales_year"] = df["sales_year"].astype(int)
    years = sorted(df["sales_year"].unique())
    stores = sorted(df["store_id"].astype(int).unique())
    selections = [("All stores", df)] + [(f"Store {s}", df[df["store_id"] == s]) for s in stores]

    fig = go.Figure()
    for k, (name, part) in enumerate(selections):
        by_year = part.groupby("sales_year")[md].sum(min_count=1).reindex(years)
        for j, col in enumerate(md):
            y = by_year[col]
            fig.add_bar(
                name=f"MarkDown{j + 1}", x=[str(yr) for yr in years], y=y.values,
                marker_color=FIVE[j], legendgroup=col, visible=(k == 0),
                text=[money(v) for v in y], textposition="outside", textfont_size=11,
                cliponaxis=False,
                hovertemplate=f"{name}, %{{x}}<br>MarkDown{j + 1}: %{{y:$,.0f}}<extra></extra>",
            )
    n = len(md)
    buttons = [
        dict(label=name, method="update",
             args=[{"visible": [i // n == k for i in range(len(fig.data))]}])
        for k, (name, _) in enumerate(selections)
    ]
    fig.update_layout(
        barmode="group",
        updatemenus=[dict(buttons=buttons, x=1, xanchor="right", y=1.02, yanchor="bottom",
                          direction="down", showactive=True)],
        xaxis_title="Year", yaxis_title="Markdown total ($)",
    )
    fig.update_xaxes(type="category", categoryorder="array",
                     categoryarray=[str(yr) for yr in years])
    if years and years[0] < 2011:
        # x=0 is the first category; a year string like "2010" would be read as a number
        fig.add_annotation(x=0, y=0, yshift=14, showarrow=False,
                           text="Not recorded", font=dict(color="#6b6b6b", size=12))
    style(fig, height=540)
    fig.update_layout(margin_t=60)
    return fig


# 6. Weekly sales by store type (share donut + total per store)
def sales_by_store_type():
    df = load("06_sales_by_store_type.sql")
    df["store_id"] = df["store_id"].astype(int)
    df = df.sort_values(["store_type", "total_sales"], ascending=[True, False])
    df["label"] = "Store " + df["store_id"].astype(str)
    share = df.groupby("store_type")["total_sales"].sum().reindex(TYPES)

    fig = make_subplots(rows=1, cols=2, column_widths=[0.34, 0.66],
                        specs=[[{"type": "domain"}, {"type": "xy"}]],
                        subplot_titles=("Share of total sales", "Total sales by store"))
    fig.add_trace(go.Pie(
        labels=[f"Type {t}" for t in TYPES], values=share.values, hole=0.55, sort=False,
        marker=dict(colors=THREE, line=dict(color="white", width=2)),
        textinfo="label+percent", textposition="outside", showlegend=False,
        hovertemplate="%{label}: %{value:$,.0f} (%{percent})<extra></extra>",
    ), row=1, col=1)
    for t, color in zip(TYPES, THREE):
        part = df[df["store_type"] == t]
        fig.add_bar(y=part["label"], x=part["total_sales"], orientation="h", name=f"Type {t}",
                    marker_color=color, row=1, col=2,
                    hovertemplate="%{y}: %{x:$,.0f}<extra>Type " + t + "</extra>")
    fig.update_yaxes(categoryorder="array", categoryarray=df["label"].tolist(),
                     autorange="reversed", tickfont_size=10, row=1, col=2)
    fig.update_xaxes(title_text="Total sales ($)", row=1, col=2)
    fig.update_layout(barmode="relative")
    style(fig, height=900, money_axis="x")
    fig.update_layout(legend=dict(x=0.36, y=-0.07, yanchor="top"), margin_b=90)
    return fig


# 7. Fuel price by year
def fuel_price_by_year():
    df = load("07_fuel_price_by_year.sql")
    df["sales_year"] = df["sales_year"].astype(int).astype(str)
    fig = px.bar(
        df, x="sales_year", y="avg_fuel_price", orientation="v",
        text=df["avg_fuel_price"].map(lambda v: f"${v:.2f}"),
        custom_data=["min_fuel_price", "max_fuel_price"], color_discrete_sequence=[BLUE],
        labels={"sales_year": "Year", "avg_fuel_price": "Average fuel price ($/gal)"},
    )
    fig.update_traces(
        textposition="outside", cliponaxis=False,
        hovertemplate="%{x}<br>Average %{y:$.2f}/gal<br>"
                      "Range %{customdata[0]:$.2f} to %{customdata[1]:$.2f}<extra></extra>",
    )
    fig.update_yaxes(range=[0, df["avg_fuel_price"].max() * 1.18])
    return style(fig, height=420)


# 8. Weekly sales by year, month and date
def sales_by_year_month_date():
    df = load("08_sales_by_year_month_date.sql")
    d = pd.to_datetime(df["store_date"])
    by_year = df.groupby(d.dt.year)["total_sales"].sum()
    by_month = df.groupby(d.dt.month)["total_sales"].sum().reindex(range(1, 13))
    by_day = df.groupby(d.dt.day)["total_sales"].sum().reindex(range(1, 32))

    fig = make_subplots(rows=2, cols=2, column_widths=[0.3, 0.7], vertical_spacing=0.16,
                        specs=[[{}, {}], [{"colspan": 2}, None]],
                        subplot_titles=("By year", "By month", "By day of month"))
    fig.add_bar(x=by_year.index.astype(str), y=by_year.values, text=[money(v) for v in by_year],
                row=1, col=1)
    fig.add_bar(x=MONTHS, y=by_month.values, text=[money(v) for v in by_month], row=1, col=2)
    fig.add_bar(x=list(by_day.index), y=by_day.values, row=2, col=1)
    fig.update_traces(marker_color=BLUE, textposition="outside", cliponaxis=False,
                      textfont_size=11, hovertemplate="%{x}: %{y:$,.0f}<extra></extra>")
    fig.update_yaxes(title_text="Total sales ($)", col=1)
    fig.update_yaxes(range=[0, by_year.max() * 1.18], row=1, col=1)
    fig.update_yaxes(range=[0, by_month.max() * 1.18], row=1, col=2)
    fig.update_xaxes(dtick=1, row=2, col=1)
    fig.update_layout(showlegend=False)
    return style(fig, height=720)


# 9. Weekly sales by CPI
def sales_by_cpi():
    df = load("09_sales_by_cpi.sql").sort_values("cpi")
    fig = px.line(df, x="cpi", y="total_sales", color_discrete_sequence=[BLUE],
                  labels={"cpi": "CPI", "total_sales": "Total sales ($)"})
    fig.update_traces(line=dict(width=1.5, dash="dot"),
                      hovertemplate="CPI %{x:.2f}<br>%{y:$,.0f}<extra></extra>")
    return style(fig)


# 10. Department-wise weekly sales
def sales_by_department():
    df = load("10_sales_by_department.sql")
    df["dept_id"] = df["dept_id"].astype(int)
    top5 = df.nlargest(5, "total_sales")["dept_id"]
    df["group"] = np.where(df["dept_id"].isin(top5), "Top 5 departments", "Other departments")
    fig = px.bar(
        df, x="dept_id", y="total_sales", color="group", orientation="v",
        category_orders={"group": ["Top 5 departments", "Other departments"]},
        color_discrete_map={"Top 5 departments": ORANGE, "Other departments": BLUE},
        labels={"dept_id": "Department", "total_sales": "Total sales ($)"},
    )
    fig.update_traces(hovertemplate="Dept %{x}: %{y:$,.0f}<extra></extra>")
    for _, row in df[df["dept_id"].isin(top5)].iterrows():
        fig.add_annotation(x=row["dept_id"], y=row["total_sales"], yanchor="bottom", yshift=4,
                           text=f"Dept {row['dept_id']}<br>{money(row['total_sales'])}",
                           showarrow=False, font=dict(size=11, color="#1f1f1f"))
    fig.update_xaxes(dtick=10)
    fig.update_yaxes(range=[min(0, df["total_sales"].min() * 1.1), df["total_sales"].max() * 1.18])
    fig.update_layout(barmode="relative")
    return style(fig, height=500)


# (title from the spec, chart function, note shown under the title)
# Once you've looked at each chart, replace its note with a one-line takeaway.
REPORTS = [
    ("Weekly sales by store and holiday", sales_by_store_holiday,
     "Total sales per store, split into holiday weeks and other weeks."),
    ("Weekly sales by temperature and year", sales_by_temperature_year,
     "Total sales by the store-week's temperature, in 10°F bands, for each year."),
    ("Weekly sales by store size", sales_by_store_size,
     "Total sales per store, ordered by store size. Hover a point for the store."),
    ("Weekly sales by store type and month", sales_by_type_month,
     "Total sales by calendar month for each store type, across all years."),
    ("Markdown sales by year and store", markdowns_by_year_store,
     "Markdown totals by year; pick a store from the menu. Markdowns are recorded "
     "from November 2011 onward."),
    ("Weekly sales by store type", sales_by_store_type,
     "Each store type's share of total sales, and total sales for every store."),
    ("Fuel price by year", fuel_price_by_year,
     "Average fuel price per year across stores (2010 to 2012). Hover for the range."),
    ("Weekly sales by year, month and date", sales_by_year_month_date,
     "Total sales by year, by month and by day of the month."),
    ("Weekly sales by CPI", sales_by_cpi,
     "Total sales at each CPI value, ordered by CPI."),
    ("Department-wise weekly sales", sales_by_department,
     "Total sales for every department, with the top five highlighted."),
]


def has_numbers(fig) -> bool:
    """True if at least one trace has real numeric values (catches the 'blank chart' case)."""
    for t in fig.data:
        if t.type == "pie":
            arr = t.values
        else:
            arr = t.x if getattr(t, "orientation", None) == "h" else t.y
        if arr is None:
            continue
        a = np.asarray(arr)
        if a.dtype.kind in "iuf" and np.isfinite(a.astype(float)).any():
            return True
    return False


def main():
    sections = []
    for i, (title, build, note) in enumerate(REPORTS, start=1):
        fig = build()
        if not has_numbers(fig):
            raise RuntimeError(f"Report {i} ({title}) has no plottable numbers; "
                               "check its query output and column types.")
        chart = fig.to_html(full_html=False, include_plotlyjs="cdn" if i == 1 else False,
                            config={"displaylogo": False, "responsive": True})
        sections.append(f"<section><h2>{i}. {title}</h2><p>{note}</p>{chart}</section>")
        print(f"  built {i}. {title}")

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>Walmart Sales Reports</title><style>"
        "body{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;color:#1f1f1f;"
        "background:#f6f6f4;max-width:1200px;margin:0 auto;padding:16px}"
        "h1{margin:8px 0 4px}header p{color:#52514e;margin:0 0 16px}"
        "section{background:#fff;border:1px solid #e4e4e0;border-radius:8px;"
        "padding:16px 16px 4px;margin:0 0 16px}"
        "h2{font-size:1.15rem;margin:0 0 4px}section p{color:#52514e;margin:0 0 8px}"
        "</style></head><body><header><h1>Walmart Sales Reports</h1>"
        "<p>Built with Snowflake, dbt and Plotly from the current version of the "
        "SCD2 fact table.</p></header>" + "".join(sections) + "</body></html>",
        encoding="utf-8",
    )
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
