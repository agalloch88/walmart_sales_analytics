select store_id, isholiday, avg(weekly_sales) as avg_weekly_sales
from walmart_store_week
group by store_id, isholiday
order by store_id, isholiday