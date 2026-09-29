with flags as (
    select store_date, is_holiday from {{ ref('stg_walmart__department_sales') }}
    union
    select store_date, is_holiday from {{ ref('stg_walmart__store_features') }}
)
select store_date, count(*) as flag_values
from flags
group by store_date
having count(*) > 1