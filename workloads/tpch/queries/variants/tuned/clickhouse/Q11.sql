-- TPC-H Query 11: Important Stock Identification (ClickHouse tuned)
-- Reuses the Germany slice once and separates the total value threshold.

WITH germany_partsupp AS (
    SELECT
        ps.ps_partkey,
        ps.ps_supplycost,
        ps.ps_availqty
    FROM partsupp ps
    INNER JOIN supplier s
        ON s.s_suppkey = ps.ps_suppkey
    INNER JOIN nation n
        ON n.n_nationkey = s.s_nationkey
    WHERE
        n.n_name = 'GERMANY'
),
total_value AS (
    SELECT
        SUM(ps_supplycost * ps_availqty) * 0.0001 AS cutoff
    FROM germany_partsupp
)
SELECT
    gp.ps_partkey,
    gp.value
FROM (
    SELECT
        ps_partkey,
        SUM(ps_supplycost * ps_availqty) AS value
    FROM germany_partsupp
    GROUP BY
        ps_partkey
) gp
CROSS JOIN total_value
WHERE
    gp.value > cutoff
ORDER BY
    gp.value DESC;
