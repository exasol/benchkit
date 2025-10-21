-- TPC-H Query 13: Customer Distribution
SELECT
    c_count,
    COUNT(*) AS custdist
FROM
    (
        SELECT
            c_custkey,
            countIf(o_comment NOT LIKE '%special%requests%') AS c_count
        FROM customer
        LEFT OUTER JOIN orders ON c_custkey = o_custkey
            -- ClickHouse handles the condition in countIf above
        GROUP BY
            c_custkey
    ) AS c_orders
GROUP BY
    c_count
ORDER BY
    custdist DESC,
    c_count DESC;