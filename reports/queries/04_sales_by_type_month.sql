select store_type, sales_month,
       avg(weekly_sales) as avg_weekly_sales
from walmart_store_week
group by store_type, sales_month
order by store_type, sales_month