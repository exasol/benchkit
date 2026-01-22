-- Aggregates lineitem once per order to identify the single late supplier
WITH order_stats AS (
    SELECT
        l_orderkey,
        arrayDistinct(groupArrayIf(l_suppkey, l_receiptdate > l_commitdate)) AS late_suppliers,
        countDistinct(l_suppkey) AS supplier_cnt
    FROM lineitem
    GROUP BY l_orderkey
    HAVING supplier_cnt > 1 AND length(late_suppliers) = 1
)
SELECT
    s.s_name,
    count() AS numwait
FROM order_stats
    ARRAY JOIN late_suppliers AS late_supp
JOIN lineitem l
    ON l.l_orderkey = order_stats.l_orderkey
    AND l.l_suppkey = late_supp
    AND l.l_receiptdate > l.l_commitdate
JOIN orders o
    ON o.o_orderkey = l.l_orderkey
    AND o.o_orderstatus = 'F'
JOIN supplier s
    ON s.s_suppkey = l.l_suppkey
JOIN nation n
    ON n.n_nationkey = s.s_nationkey
    AND n.n_name = 'SAUDI ARABIA'
GROUP BY
    s.s_name
ORDER BY
    numwait DESC,
    s.s_name
LIMIT 100;