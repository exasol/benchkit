-- TPC-H Query 20: Potential Part Promotion (ClickHouse tuned)
-- Pre-aggregates matching lineitem rows once to avoid correlated subqueries.

WITH forest_parts AS (
    SELECT
        p_partkey
    FROM part
    WHERE p_name LIKE 'forest%'
),
lineitem_1994 AS (
    SELECT
        l_partkey,
        l_suppkey,
        SUM(l_quantity) AS supplied_qty
    FROM lineitem
    WHERE
        l_shipdate >= DATE '1994-01-01'
        AND l_shipdate < DATE '1994-01-01' + INTERVAL '1' YEAR
    GROUP BY
        l_partkey,
        l_suppkey
),
qualified_suppliers AS (
    SELECT DISTINCT
        ps.ps_suppkey
    FROM partsupp ps
    INNER JOIN forest_parts fp
        ON ps.ps_partkey = fp.p_partkey
    INNER JOIN lineitem_1994 li
        ON li.l_partkey = ps.ps_partkey
        AND li.l_suppkey = ps.ps_suppkey
    WHERE
        ps.ps_availqty > 0.5 * li.supplied_qty
)
SELECT
    s.s_name,
    s.s_address
FROM qualified_suppliers qs
INNER JOIN supplier s
    ON s.s_suppkey = qs.ps_suppkey
INNER JOIN nation n
    ON n.n_nationkey = s.s_nationkey
WHERE
    n.n_name = 'CANADA'
ORDER BY
    s.s_name;