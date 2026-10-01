{{ config(
    materialized = 'incremental',
    incremental_strategy = 'merge',
    unique_key = ['store_id', 'dept_id'],
    merge_exclude_columns = ['insert_date'],
    on_schema_change = 'fail'
) }}

with store_depts as (
    select distinct store_id, dept_id
    from {{ ref('stg_walmart__department_sales') }}
),

final as (
    select
        sd.store_id,
        sd.dept_id,
        s.store_type,
        s.store_size,
        current_timestamp()::timestamp_ntz as insert_date,
        current_timestamp()::timestamp_ntz as update_date
    from store_depts sd
    left join {{ ref('stg_walmart__stores') }} s
      on s.store_id = sd.store_id
)

select f.* from final f
{% if is_incremental() %}
where not exists (
    select 1 from {{ this }} t
    where t.store_id = f.store_id
      and t.dept_id  = f.dept_id
      and equal_null(t.store_type, f.store_type)
      and equal_null(t.store_size, f.store_size)
)
{% endif %}