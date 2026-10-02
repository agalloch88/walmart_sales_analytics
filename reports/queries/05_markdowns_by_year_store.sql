select sales_year, store_id,
       sum(markdown1) as markdown1, sum(markdown2) as markdown2,
       sum(markdown3) as markdown3, sum(markdown4) as markdown4,
       sum(markdown5) as markdown5
from walmart_store_week
where coalesce(markdown1, markdown2, markdown3, markdown4, markdown5) is not null
group by sales_year, store_id
order by sales_year, store_id