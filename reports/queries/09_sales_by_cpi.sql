select cpi, sum(weekly_sales) as total_sales
from walmart_store_week
where cpi is not null
group by cpi
order by cpi
