select
    store::int     as store_id,
    date           as store_date,
    temperature    as store_temperature,
    fuel_price,
    markdown1,
    markdown2,
    markdown3,
    markdown4,
    markdown5,
    cpi,
    unemployment,
    isholiday      as is_holiday
from {{ source('walmart_raw', 'fact') }}