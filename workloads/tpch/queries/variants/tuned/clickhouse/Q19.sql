-- TPC-H Query 19: Discounted Revenue (ClickHouse tuned)
-- Breaks the OR-heavy predicate into disjoint UNION ALL branches
-- to keep per-branch predicates selective while preserving semantics.

WITH filtered AS (
    SELECT
        l_extendedprice,
        l_discount,
        l_quantity,
        p_brand,
        p_container,
        p_size
    FROM lineitem
    INNER JOIN part ON p_partkey = l_partkey
    WHERE
        l_shipmode IN ('AIR', 'AIR REG')
        AND l_shipinstruct = 'DELIVER IN PERSON'
        AND p_brand IN ('Brand#12', 'Brand#23', 'Brand#34')
        AND p_container IN (
            'SM CASE', 'SM BOX', 'SM PACK', 'SM PKG',
            'MED BAG', 'MED BOX', 'MED PKG', 'MED PACK',
            'LG CASE', 'LG BOX', 'LG PACK', 'LG PKG'
        )
)
SELECT
    SUM(revenue) AS revenue
FROM (
    SELECT
        l_extendedprice * (1 - l_discount) AS revenue
    FROM filtered
    WHERE
        p_brand = 'Brand#12'
        AND p_container IN ('SM CASE', 'SM BOX', 'SM PACK', 'SM PKG')
        AND l_quantity BETWEEN 1 AND 11
        AND p_size BETWEEN 1 AND 5

    UNION ALL

    SELECT
        l_extendedprice * (1 - l_discount) AS revenue
    FROM filtered
    WHERE
        p_brand = 'Brand#23'
        AND p_container IN ('MED BAG', 'MED BOX', 'MED PKG', 'MED PACK')
        AND l_quantity BETWEEN 10 AND 20
        AND p_size BETWEEN 1 AND 10

    UNION ALL

    SELECT
        l_extendedprice * (1 - l_discount) AS revenue
    FROM filtered
    WHERE
        p_brand = 'Brand#34'
        AND p_container IN ('LG CASE', 'LG BOX', 'LG PACK', 'LG PKG')
        AND l_quantity BETWEEN 20 AND 30
        AND p_size BETWEEN 1 AND 15
) AS revenue_partitioned;
