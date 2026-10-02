select store_id, store_type, store_size,
       avg(weekly_sales) as avg_weekly_sales
from walmart_store_week
group by store_id, store_type, store_size
order by store_size