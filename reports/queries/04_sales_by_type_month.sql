select store_type, sales_month, sum(weekly_sales) as total_sales
from walmart_store_week
group by store_type, sales_month
order by store_type, sales_month
