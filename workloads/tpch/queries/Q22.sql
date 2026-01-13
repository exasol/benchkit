-- TPC-H Query 22: Global Sales Opportunity
SELECT
    cntrycode,
    COUNT(*) AS numcust,
    SUM(c_acctbal) AS totacctbal
FROM (
    SELECT
        SUBSTRING(c_phone FROM 1 FOR 2) AS cntrycode,
        c_acctbal
    FROM customer
    WHERE
        {% if system_kind == 'trino' %}
        SUBSTRING(c_phone FROM 1 FOR 2) IN ('13', '31', '23', '29', '30', '18', '17')
        {% else %}
        SUBSTRING(c_phone FROM 1 FOR 2) IN (13, 31, 23, 29, 30, 18, 17)
        {% endif %}
        AND c_acctbal > (
            SELECT
                AVG(c_acctbal)
            FROM customer
            WHERE
                c_acctbal > 0.00
                {% if system_kind == 'trino' %}
                AND SUBSTRING(c_phone FROM 1 FOR 2) IN ('13', '31', '23', '29', '30', '18', '17')
                {% else %}
                AND SUBSTRING(c_phone FROM 1 FOR 2) IN (13, 31, 23, 29, 30, 18, 17)
                {% endif %}
        )
        AND NOT EXISTS (
            SELECT
                *
            FROM orders
            WHERE
                o_custkey = c_custkey
        )
    ) AS custsale
GROUP BY
    cntrycode
ORDER BY
    cntrycode;