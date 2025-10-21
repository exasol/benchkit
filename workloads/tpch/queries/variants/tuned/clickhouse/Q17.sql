-- TPC-H Query 17: Small-Quantity-Order Revenue (ClickHouse tuned)
-- Precomputes per-part average quantities for the filtered part set.

WITH target_parts AS (
    SELECT
        p_partkey
    FROM part
    WHERE
        p_brand = 'Brand#23'
        AND p_container = 'MED BOX'
),
avg_quantity_by_part AS (
    SELECT
        l.l_partkey,
        AVG(l.l_quantity) AS avg_qty
    FROM lineitem l
    INNER JOIN target_parts tp
        ON tp.p_partkey = l.l_partkey
    GROUP BY
        l.l_partkey
)
SELECT
    SUM(l.l_extendedprice) / 7.0 AS avg_yearly
FROM lineitem l
INNER JOIN target_parts tp
    ON tp.p_partkey = l.l_partkey
INNER JOIN avg_quantity_by_part aq
    ON aq.l_partkey = l.l_partkey
WHERE
    l.l_quantity < 0.2 * aq.avg_qty;
