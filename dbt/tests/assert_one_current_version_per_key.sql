select store_id, dept_id, date_id, count(*) as current_rows
from {{ ref('walmart_fact_table') }}
where vrsn_end_date = '9999-12-31'
group by 1, 2, 3
having count(*) <> 1