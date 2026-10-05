select store_type, store_id, sum(weekly_sales) as total_sales
from walmart_store_week
group by store_type, store_id
order by store_type, total_sales desc
