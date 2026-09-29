select
    store::int     as store_id,
    dept::int      as dept_id,
    date           as store_date,
    weekly_sales,
    isholiday      as is_holiday
from {{ source('walmart_raw', 'department') }}