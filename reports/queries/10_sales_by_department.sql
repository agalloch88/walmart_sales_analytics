select dept_id, sum(store_weekly_sales) as total_sales
from walmart_fact_current
group by dept_id
order by dept_id
