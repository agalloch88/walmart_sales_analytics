with sales as (
    select * from {{ ref('stg_walmart__department_sales') }}
),

features as (
    select * from {{ ref('stg_walmart__store_features') }}
),

stores as (
    select * from {{ ref('stg_walmart__stores') }}
)

select
    s.store_id,
    s.dept_id,
    {{ to_date_id('s.store_date') }}               as date_id,
    st.store_size,
    s.weekly_sales                                 as store_weekly_sales,
    f.fuel_price,
    f.store_temperature,
    f.unemployment,
    f.cpi,
    f.markdown1,
    f.markdown2,
    f.markdown3,
    f.markdown4,
    f.markdown5,
    current_timestamp()::timestamp_ntz             as insert_date,
    current_timestamp()::timestamp_ntz             as update_date
from sales s
left join features f
  on  f.store_id   = s.store_id
  and f.store_date = s.store_date
left join stores st
  on  st.store_id  = s.store_id