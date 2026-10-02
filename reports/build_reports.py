"""Build docs/index.html: one Plotly chart per required report, read from Snowflake."""
from pathlib import Path

import plotly.express as px

from db import query_df

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "index.html"

STORE_TYPES = {"store_type": ["A", "B", "C"]}


def load(sql_file: str):
    return query_df((HERE / "queries" / sql_file).read_text())


def as_text(df, *cols):
    """Make years and IDs categories, so Plotly gives each its own color, box or bar."""
    for col in cols:
        df[col] = df[col].astype(str)
    return df


# 1
def sales_by_store_holiday():
    df = load("01_sales_by_store_holiday.sql")
    df["isholiday"] = df["isholiday"].map({"Y": "Holiday weeks", "N": "Other weeks"})
    return px.bar(
        df, x="store_id", y="avg_weekly_sales", color="isholiday", barmode="group",
        labels={"store_id": "Store", "avg_weekly_sales": "Avg weekly sales ($)",
                "isholiday": ""},
    )


# 2
def sales_by_temperature_year():
    df = as_text(load("02_sales_by_temperature_year.sql"), "sales_year")
    return px.scatter(
        df, x="temperature", y="weekly_sales", color="sales_year", opacity=0.5,
        hover_data=["store_id", "store_date"],
        labels={"temperature": "Temperature (F)", "weekly_sales": "Store weekly sales ($)",
                "sales_year": "Year"},
    )


# 3
def sales_by_store_size():
    df = load("03_sales_by_store_size.sql")
    return px.scatter(
        df, x="store_size", y="avg_weekly_sales", color="store_type",
        category_orders=STORE_TYPES, hover_data=["store_id"],
        labels={"store_size": "Store size (sq ft)", "avg_weekly_sales": "Avg weekly sales ($)",
                "store_type": "Store type"},
    )


# 4
def sales_by_type_month():
    df = load("04_sales_by_type_month.sql")
    fig = px.line(
        df, x="sales_month", y="avg_weekly_sales", color="store_type", markers=True,
        category_orders=STORE_TYPES,
        labels={"sales_month": "Month", "avg_weekly_sales": "Avg store weekly sales ($)",
                "store_type": "Store type"},
    )
    fig.update_xaxes(dtick=1)
    return fig


# 5
def markdowns_by_year_store():
    df = load("05_markdowns_by_year_store.sql")
    long = df.melt(id_vars=["sales_year", "store_id"], var_name="markdown", value_name="amount")
    fig = px.bar(
        long, x="store_id", y="amount", color="markdown", facet_row="sales_year",
        labels={"store_id": "Store", "amount": "Markdown ($)", "markdown": "",
                "sales_year": "Year"},
    )
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))  # "2011", not "Year=2011"
    fig.update_layout(height=640)
    return fig


# 6
def sales_by_store_type():
    df = load("06_sales_by_store_type.sql")
    return px.box(
        df, x="store_type", y="weekly_sales", category_orders=STORE_TYPES,
        labels={"store_type": "Store type", "weekly_sales": "Store weekly sales ($)"},
    )


# 7
def fuel_price_by_year():
    df = as_text(load("07_fuel_price_by_year.sql"), "sales_year")
    return px.box(
        df, x="sales_year", y="fuel_price",
        labels={"sales_year": "Year", "fuel_price": "Fuel price ($/gal)"},
    )


# 8
def sales_by_year_month_date():
    df = as_text(load("08_sales_by_year_month_date.sql"), "sales_year")
    return px.line(
        df, x="week_of_year", y="total_weekly_sales", color="sales_year",
        hover_data=["store_date", "sales_month"],
        labels={"week_of_year": "Week of year", "total_weekly_sales": "Total weekly sales ($)",
                "sales_year": "Year"},
    )


# 9
def sales_by_cpi():
    df = load("09_sales_by_cpi.sql")
    return px.scatter(
        df, x="cpi", y="weekly_sales", opacity=0.5, hover_data=["store_id", "store_date"],
        labels={"cpi": "CPI", "weekly_sales": "Store weekly sales ($)"},
    )


# 10
def sales_by_department():
    df = as_text(load("10_sales_by_department.sql"), "dept_id")
    fig = px.bar(
        df, x="total_sales", y="dept_id", orientation="h",
        labels={"total_sales": "Total sales ($)", "dept_id": "Department"},
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_layout(height=600)
    return fig


# (title from the spec, chart function, note shown under the title)
REPORTS = [
    ("Weekly sales by store and holiday", sales_by_store_holiday,
     "Average store-week sales per store, holiday weeks vs. other weeks."),
    ("Weekly sales by temperature and year", sales_by_temperature_year,
     "One point per store-week."),
    ("Weekly sales by store size", sales_by_store_size,
     "One point per store: average weekly sales against floor size."),
    ("Weekly sales by store type and month", sales_by_type_month,
     "Average store-week sales by calendar month, across all years."),
    ("Markdown sales by year and store", markdowns_by_year_store,
     "Markdowns are recorded from November 2011 onward."),
    ("Weekly sales by store type", sales_by_store_type,
     "Distribution of store-week sales for each store type."),
    ("Fuel price by year", fuel_price_by_year,
     "Store-week fuel prices for weeks with sales data (2010 to 2012)."),
    ("Weekly sales by year, month and date", sales_by_year_month_date,
     "Total sales across all stores per week, one line per year."),
    ("Weekly sales by CPI", sales_by_cpi,
     "One point per store-week."),
    ("Department-wise weekly sales", sales_by_department,
     "Top 20 departments by total sales."),
]


def main():
    sections = []
    for i, (title, build, note) in enumerate(REPORTS):
        fig = build()
        if fig.layout.height is None:
            fig.update_layout(height=480)
        fig.update_layout(margin=dict(t=30))
        chart = fig.to_html(full_html=False, include_plotlyjs="cdn" if i == 0 else False)
        sections.append(f"<section><h2>{i + 1}. {title}</h2><p>{note}</p>{chart}</section>")

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>Walmart Sales Reports</title>"
        "<style>body{font-family:system-ui,sans-serif;max-width:1100px;"
        "margin:0 auto;padding:16px}</style></head><body>"
        "<h1>Walmart Sales Reports</h1>" + "".join(sections) + "</body></html>",
        encoding="utf-8",
    )
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()