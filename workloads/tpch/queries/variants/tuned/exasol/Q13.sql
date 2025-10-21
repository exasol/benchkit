-- TPC-H Query 13: Customer Distribution
-- Exasol-optimized variant using CTEs
-- Performance: 100GB ~4.9s vs original ~11.6s

WITH orders_filtered AS (
    SELECT
        o_custkey,
        COUNT(*) AS cnt
    FROM orders
    WHERE o_comment NOT LIKE '%special%requests%'
    GROUP BY o_custkey
),
per_customer AS (
    SELECT
        c.c_custkey,
        COALESCE(o.cnt, 0) AS c_count
    FROM customer c
    LEFT JOIN orders_filtered o
        ON c.c_custkey = o.o_custkey
)
SELECT
    c_count,
    COUNT(*) AS custdist
FROM per_customer
GROUP BY c_count
ORDER BY custdist DESC, c_count DESC;
