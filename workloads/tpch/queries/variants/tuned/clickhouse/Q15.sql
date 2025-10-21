-- TPC-H Query 15: Top Supplier (ClickHouse tuned)
-- Computes revenue once and shares the max via a separate CTE.

WITH revenue AS (
    SELECT
        l_suppkey AS supplier_no,
        SUM(l_extendedprice * (1 - l_discount)) AS total_revenue
    FROM lineitem
    WHERE
        l_shipdate >= DATE '1996-01-01'
        AND l_shipdate < DATE '1996-01-01' + INTERVAL '3' MONTH
    GROUP BY
        l_suppkey
),
max_revenue AS (
    SELECT
        MAX(total_revenue) AS max_total_revenue
    FROM revenue
)
SELECT
    s.s_suppkey,
    s.s_name,
    s.s_address,
    s.s_phone,
    r.total_revenue
FROM revenue r
INNER JOIN supplier s
    ON s.s_suppkey = r.supplier_no
CROSS JOIN max_revenue m
WHERE
    r.total_revenue = m.max_total_revenue
ORDER BY
    s.s_suppkey;
