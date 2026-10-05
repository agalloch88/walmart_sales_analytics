select store_date, sum(weekly_sales) as total_sales
from walmart_store_week
group by store_date
order by store_date
