{{ config(
    materialized = 'incremental',
    incremental_strategy = 'merge',
    unique_key = 'date_id',
    merge_exclude_columns = ['insert_date'],
    on_schema_change = 'fail'
) }}

with dates as (
    select store_date, is_holiday from {{ ref('stg_walmart__department_sales') }}
    union
    select store_date, is_holiday from {{ ref('stg_walmart__store_features') }}
),

final as (
    select
        {{ to_date_id('store_date') }}              as date_id,
        store_date,
        iff(is_holiday, 'Y', 'N')                   as isholiday,
        current_timestamp()::timestamp_ntz          as insert_date,
        current_timestamp()::timestamp_ntz          as update_date
    from dates
)

select f.* from final f
{% if is_incremental() %}
where not exists (
    select 1 from {{ this }} t
    where t.date_id = f.date_id
      and t.isholiday = f.isholiday   -- one line per tracked column
)
{% endif %}