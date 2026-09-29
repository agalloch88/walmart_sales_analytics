select
    store::int          as store_id,
    upper(trim(type))   as store_type,
    size::int           as store_size
from {{ source('walmart_raw', 'stores') }}