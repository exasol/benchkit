-- Query 3
-- Description: Uses window functions to fetch line item details along with the extended price of the next item, the ship date of the previous item, and the extended price of the first item within the same order.
-- Difficulty: Medium
SELECT
    L_ORDERKEY,
    L_LINENUMBER,
    L_SHIPDATE,
    L_EXTENDEDPRICE,
    LEAD(L_EXTENDEDPRICE) OVER (PARTITION BY L_ORDERKEY ORDER BY L_LINENUMBER) AS next_line_price,
    LAG(L_SHIPDATE) OVER (PARTITION BY L_ORDERKEY ORDER BY L_LINENUMBER) AS prev_ship_date,
    FIRST_VALUE(L_EXTENDEDPRICE) OVER (PARTITION BY L_ORDERKEY ORDER BY L_LINENUMBER) AS first_line_price
FROM lineitem
-- tuned: apply orderby/limit before the expensive window function
WHERE L_ORDERKEY <= (
	SELECT L_ORDERKEY
	FROM lineitem
	ORDER BY L_ORDERKEY, L_LINENUMBER
	LIMIT 1 OFFSET 1000
)
ORDER BY L_ORDERKEY, L_LINENUMBER
LIMIT 1000;
