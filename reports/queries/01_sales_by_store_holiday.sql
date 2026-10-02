select store_id, isholiday, sum(weekly_sales) as total_sales
from walmart_store_week
group by store_id, isholiday
order by store_id, isholiday
