{{ config(materialized='view') }}

select
    store_id,
    store_date,
    any_value(sales_year)         as sales_year,
    any_value(sales_month)        as sales_month,
    any_value(week_of_year)       as week_of_year,
    any_value(isholiday)          as isholiday,
    any_value(store_type)         as store_type,
    any_value(store_size)         as store_size,
    sum(store_weekly_sales)       as weekly_sales,
    any_value(store_temperature)  as temperature,
    any_value(fuel_price)         as fuel_price,
    any_value(cpi)                as cpi,
    any_value(unemployment)       as unemployment,
    any_value(markdown1)          as markdown1,
    any_value(markdown2)          as markdown2,
    any_value(markdown3)          as markdown3,
    any_value(markdown4)          as markdown4,
    any_value(markdown5)          as markdown5
from {{ ref('walmart_fact_current') }}
group by store_id, store_date