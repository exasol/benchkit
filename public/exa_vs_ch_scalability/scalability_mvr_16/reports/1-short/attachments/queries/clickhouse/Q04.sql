-- TPC-H Query 4: Order Priority Checking (ClickHouse tuned)
-- Identifies late shipments once and semi-joins against orders to avoid correlated scans.

WITH late_orders AS (
    SELECT DISTINCT
        l_orderkey AS o_orderkey
    FROM lineitem
    WHERE
        l_commitdate < l_receiptdate
)
SELECT
    o.o_orderpriority,
    count() AS order_count
FROM orders o
ANY INNER JOIN late_orders lo USING (o_orderkey)
WHERE
    o.o_orderdate >= DATE '1993-07-01'
    AND o.o_orderdate < DATE '1993-07-01' + INTERVAL '3' MONTH
GROUP BY
    o.o_orderpriority
ORDER BY
    o.o_orderpriority;