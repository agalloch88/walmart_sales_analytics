{{ config(materialized='view') }}

select
    f.store_id,
    f.dept_id,
    f.date_id,
    d.store_date,
    year(d.store_date)        as sales_year,
    month(d.store_date)       as sales_month,
    weekofyear(d.store_date)  as week_of_year,
    d.isholiday,
    s.store_type,
    f.store_size,
    f.store_weekly_sales,
    f.fuel_price,
    f.store_temperature,
    f.unemployment,
    f.cpi,
    f.markdown1,
    f.markdown2,
    f.markdown3,
    f.markdown4,
    f.markdown5
from {{ ref('walmart_fact_table') }} f
join {{ ref('walmart_date_dim') }} d
  on d.date_id = f.date_id
join {{ ref('walmart_store_dim') }} s
  on  s.store_id = f.store_id
  and s.dept_id  = f.dept_id
where f.vrsn_end_date = '9999-12-31'