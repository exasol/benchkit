-- TPC-H Query 22: Global Sales Opportunity (ClickHouse tuned)
-- Separates the average calculation and uses an ANTI JOIN to drop customers with orders.

WITH
    ['13', '31', '23', '29', '30', '18', '17'] AS prefixes,
    (
        SELECT
            AVG(c_acctbal)
        FROM customer
        WHERE
            c_acctbal > 0
            AND substring(c_phone, 1, 2) IN prefixes
    ) AS avg_positive_balance
SELECT
    eligible.cntrycode,
    count() AS numcust,
    SUM(eligible.c_acctbal) AS totacctbal
FROM (
    SELECT
        substring(c_phone, 1, 2) AS cntrycode,
        c_custkey,
        c_acctbal
    FROM customer
    WHERE
        substring(c_phone, 1, 2) IN prefixes
        AND c_acctbal > avg_positive_balance
) AS eligible
LEFT ANTI JOIN orders o
    ON o.o_custkey = eligible.c_custkey
GROUP BY
    eligible.cntrycode
ORDER BY
    eligible.cntrycode;