select sales_year,
       floor(temperature / 10) * 10 as temp_band,
       sum(weekly_sales)            as total_sales
from walmart_store_week
where temperature is not null
group by sales_year, temp_band
order by sales_year, temp_band
