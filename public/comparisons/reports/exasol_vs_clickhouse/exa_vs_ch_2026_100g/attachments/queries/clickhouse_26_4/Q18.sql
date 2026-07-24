-- TPC-H Query 18: Large Volume Customer (ClickHouse tuned)
-- Uses a semi-join friendly CTE for qualifying orders to avoid repeated aggregation.

WITH big_orders AS (
    SELECT
        l_orderkey
    FROM lineitem
    GROUP BY
        l_orderkey
    HAVING
        SUM(l_quantity) > 300
)
SELECT
    c.c_name,
    c.c_custkey,
    o.o_orderkey,
    o.o_orderdate,
    o.o_totalprice,
    SUM(l.l_quantity) AS sum_qty
FROM big_orders bo
INNER JOIN orders o
    ON o.o_orderkey = bo.l_orderkey
INNER JOIN customer c
    ON c.c_custkey = o.o_custkey
INNER JOIN lineitem l
    ON l.l_orderkey = bo.l_orderkey
GROUP BY
    c.c_name,
    c.c_custkey,
    o.o_orderkey,
    o.o_orderdate,
    o.o_totalprice
ORDER BY
    o.o_totalprice DESC,
    o.o_orderdate
LIMIT 100;