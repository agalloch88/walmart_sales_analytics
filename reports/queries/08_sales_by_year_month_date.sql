select store_date, sales_year, sales_month, week_of_year,
       sum(weekly_sales) as total_weekly_sales
from walmart_store_week
group by store_date, sales_year, sales_month, week_of_year
order by store_date