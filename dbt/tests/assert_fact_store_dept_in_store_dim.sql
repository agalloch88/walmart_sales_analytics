select f.store_id, f.dept_id
from {{ ref('walmart_fact_table') }} f
left join {{ ref('walmart_store_dim') }} d
  on  d.store_id = f.store_id
  and d.dept_id  = f.dept_id
where d.store_id is null