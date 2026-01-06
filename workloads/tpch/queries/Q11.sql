-- TPC-H Query 11: Important Stock Identification
{% if system_kind in ['exasol', 'trino'] %}
SELECT
    ps_partkey,
    SUM(ps_supplycost * ps_availqty) AS "value"
FROM
    partsupp,
    supplier,
    nation
WHERE
    ps_suppkey = s_suppkey
    AND s_nationkey = n_nationkey
    AND n_name = 'GERMANY'
GROUP BY
    ps_partkey
HAVING
    SUM(ps_supplycost * ps_availqty) > (
        SELECT
            SUM(ps_supplycost * ps_availqty) * 0.0001
        FROM
            partsupp,
            supplier,
            nation
        WHERE
            ps_suppkey = s_suppkey
            AND s_nationkey = n_nationkey
            AND n_name = 'GERMANY'
    )
ORDER BY
    "value" DESC;
{% elif system_kind == 'clickhouse' %}
SELECT
    ps_partkey,
    SUM(ps_supplycost * ps_availqty) AS value
FROM
    partsupp
    CROSS JOIN supplier
    CROSS JOIN nation
WHERE
    ps_suppkey = s_suppkey
    AND s_nationkey = n_nationkey
    AND n_name = 'GERMANY'
GROUP BY
    ps_partkey
HAVING
    SUM(ps_supplycost * ps_availqty) > (
        SELECT
            SUM(ps_supplycost * ps_availqty) * 0.0001
        FROM
            partsupp
            CROSS JOIN supplier
            CROSS JOIN nation
        WHERE
            ps_suppkey = s_suppkey
            AND s_nationkey = n_nationkey
            AND n_name = 'GERMANY'
    )
ORDER BY
    value DESC;
{% else %}
{{ UNSUPPORTED_SYSTEM_KIND_ERROR_FOR[system_kind] }}
{% endif %}