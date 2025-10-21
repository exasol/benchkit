-- TPC-H Query 16: Parts/Supplier Relationship (ClickHouse tuned)
-- Materializes complaint suppliers once and uses an ANTI JOIN to exclude them.

WITH complaint_suppliers AS (
    SELECT DISTINCT
        s_suppkey
    FROM supplier
    WHERE
        s_comment LIKE '%Customer%Complaints%'
)
SELECT
    p.p_brand,
    p.p_type,
    p.p_size,
    COUNT(DISTINCT ps.ps_suppkey) AS supplier_cnt
FROM part p
INNER JOIN partsupp ps
    ON p.p_partkey = ps.ps_partkey
ANTI JOIN complaint_suppliers cs
    ON cs.s_suppkey = ps.ps_suppkey
WHERE
    p.p_brand <> 'Brand#45'
    AND p.p_type NOT LIKE 'MEDIUM POLISHED%'
    AND p.p_size IN (49, 14, 23, 45, 19, 3, 36, 9)
GROUP BY
    p.p_brand,
    p.p_type,
    p.p_size
ORDER BY
    supplier_cnt DESC,
    p.p_brand,
    p.p_type,
    p.p_size;
