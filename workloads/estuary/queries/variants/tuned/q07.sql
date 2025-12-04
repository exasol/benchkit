-- Query 7
-- Description: Filters for top customers based on spending or quantity per month and then identifies those whose numeric digits within their name sum to an odd number using string manipulation and TRY_CAST.
-- Difficulty: Hard
WITH customer_sales AS (
    SELECT
        TO_CHAR(O.O_ORDERDATE, 'yyyy - MMMM') AS order_month,
        C.C_NAME AS C_NAME,
        SUM(CAST(O.O_TOTALPRICE AS FLOAT)) AS total_spent,
        SUM(CAST(L.L_QUANTITY AS INT)) AS total_quantity,
        RANK() OVER (PARTITION BY TO_CHAR(O.O_ORDERDATE, 'yyyy - MMMM') ORDER BY SUM(CAST(O.O_TOTALPRICE AS FLOAT)) DESC) AS price_rank,
        RANK() OVER (PARTITION BY TO_CHAR(O.O_ORDERDATE, 'yyyy - MMMM') ORDER BY SUM(CAST(L.L_QUANTITY AS INT)) DESC) AS quantity_rank
    FROM orders O
    JOIN lineitem L
        ON O.O_ORDERKEY = L.L_ORDERKEY
    JOIN customer C
        ON O.O_CUSTKEY = C.C_CUSTKEY
    GROUP BY TO_CHAR(O.O_ORDERDATE, 'yyyy - MMMM'), C.C_NAME
),
digit_sum_calc AS (
    SELECT
        order_month, C_NAME, total_spent, total_quantity, price_rank, quantity_rank, customer_number,
        -- tuned: Lua UDF
        quersumme(C_NAME) AS number_sum
    FROM customer_sales
)
SELECT order_month, C_NAME, total_spent, total_quantity, price_rank, quantity_rank
FROM digit_sum_calc
WHERE (price_rank <= 3 OR quantity_rank <= 3)
AND MOD(number_sum, 2) = 1
ORDER BY order_month, price_rank, quantity_rank
LIMIT 1000;
