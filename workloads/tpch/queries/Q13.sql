-- TPC-H Query 13: Customer Distribution
SELECT
    c_count,
    COUNT(*) AS custdist
FROM
    (
        SELECT
            c_custkey,
            {% if system_kind == 'exasol' %}
            COUNT(o_orderkey) AS c_count
            {% elif system_kind == 'clickhouse' %}
            countIf(o_comment NOT LIKE '%special%requests%') AS c_count
            {% else %}
            {{ UNSUPPORTED_SYSTEM_KIND_ERROR_FOR[system_kind] }}
            {% endif %}
        FROM customer
        LEFT OUTER JOIN orders ON c_custkey = o_custkey
            {% if system_kind == 'exasol' %}
            AND o_comment NOT LIKE '%special%requests%'
            {% elif system_kind == 'clickhouse' %}
            -- ClickHouse handles the condition in countIf above
            {% endif %}
        GROUP BY
            c_custkey
    ) AS c_orders
GROUP BY
    c_count
ORDER BY
    custdist DESC,
    c_count DESC;