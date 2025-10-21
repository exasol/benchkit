-- TPC-H Query 17: Small-Quantity-Order Revenue
-- Exasol-optimized variant using CTEs and window functions
-- Performance: 100GB ~0.2s vs original ~39s

WITH parts AS (
    SELECT p_partkey
    FROM part
    WHERE p_brand = 'Brand#23'
        AND p_container = 'MED BOX'
),
li AS (
    SELECT
        li.l_extendedprice,
        li.l_quantity,
        0.2 * AVG(li.l_quantity) OVER (PARTITION BY li.l_partkey) AS qty_thresh
    FROM lineitem li
    JOIN parts p ON p.p_partkey = li.l_partkey
)
SELECT SUM(l_extendedprice) / 7.0 AS avg_yearly
FROM li
WHERE l_quantity < qty_thresh;
