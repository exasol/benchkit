-- Query 5
-- Description: Ranks customers by total revenue and total quantity ordered within each month using window functions and filters for the top 3 customers in either ranking.
-- Difficulty: Medium
WITH customer_sales AS (
    SELECT
        TO_CHAR(O.O_ORDERDATE, 'yyyy - MMMM') AS order_month,
        C.C_NAME,
        SUM(O.O_TOTALPRICE) AS total_spent,
        SUM(L.L_QUANTITY) AS total_quantity,
        RANK() OVER (PARTITION BY TO_CHAR(O.O_ORDERDATE, 'yyyy - MMMM') ORDER BY SUM(O.O_TOTALPRICE) DESC) AS price_rank,
        RANK() OVER (PARTITION BY TO_CHAR(O.O_ORDERDATE, 'yyyy - MMMM') ORDER BY SUM(L.L_QUANTITY) DESC) AS quantity_rank
    FROM orders O
    JOIN lineitem L ON O.O_ORDERKEY = L.L_ORDERKEY
    JOIN customer C ON O.O_CUSTKEY = C.C_CUSTKEY
    GROUP BY TO_CHAR(O.O_ORDERDATE, 'yyyy - MMMM'), C.C_NAME
)
SELECT order_month, C_NAME, total_spent, total_quantity, price_rank, quantity_rank
FROM customer_sales
WHERE price_rank <= 3 OR quantity_rank <= 3
ORDER BY order_month, price_rank, quantity_rank
LIMIT 1000;
