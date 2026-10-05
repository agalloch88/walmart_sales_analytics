select store_id, store_type, store_size, sum(weekly_sales) as total_sales
from walmart_store_week
group by store_id, store_type, store_size
order by store_size
