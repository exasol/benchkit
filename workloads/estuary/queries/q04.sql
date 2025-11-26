
-- Query 4
-- Description: Joins lineitem and orders tables, aggregates data by shipping year/month, ship mode, and order priority, and then applies row numbering based on aggregated sums and averages within partitions.
-- Difficulty: Medium
WITH base_table AS (
    SELECT
        DATE_FORMAT(L_SHIPDATE, 'yyyy-MM') AS ship_year_month,
        L_SHIPMODE AS L_SHIPMODE,
        O_ORDERPRIORITY AS order_priority,
        COUNT(*) AS count_of_line_items,
        SUM(CAST(L_EXTENDEDPRICE AS FLOAT)) AS sum,
        AVG(CAST(L_DISCOUNT AS FLOAT)) AS avg
    FROM lineitem LI
    LEFT JOIN orders ORD
        ON LI.L_ORDERKEY = ORD.O_ORDERKEY
    GROUP BY ship_year_month, L_SHIPMODE, order_priority
)
SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY order_priority ORDER BY sum) AS row_number_by_order_priority,
    ROW_NUMBER() OVER (PARTITION BY L_SHIPMODE ORDER BY avg) AS row_number_by_ship_mode
FROM base_table
LIMIT 1000;

