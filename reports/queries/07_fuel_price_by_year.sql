select sales_year,
       avg(fuel_price) as avg_fuel_price,
       min(fuel_price) as min_fuel_price,
       max(fuel_price) as max_fuel_price
from walmart_store_week
group by sales_year
order by sales_year
