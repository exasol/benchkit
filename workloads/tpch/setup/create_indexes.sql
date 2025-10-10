-- TPC-H Index Creation Script
-- Creates indexes to optimize query performance for both database systems

{% if system_kind == 'exasol' %}
-- Create local indexes for Exasol
ENFORCE LOCAL INDEX ON {{ schema }}.lineitem (l_suppkey);
ENFORCE LOCAL INDEX ON {{ schema }}.lineitem (l_partkey, l_suppkey);
ENFORCE LOCAL INDEX ON {{ schema }}.lineitem (l_partkey);
ENFORCE LOCAL INDEX ON {{ schema }}.lineitem (l_orderkey);
ENFORCE LOCAL INDEX ON {{ schema }}.nation (n_nationkey);
ENFORCE LOCAL INDEX ON {{ schema }}.region (r_regionkey);
ENFORCE LOCAL INDEX ON {{ schema }}.supplier (s_suppkey);
ENFORCE LOCAL INDEX ON {{ schema }}.supplier (s_nationkey);
ENFORCE LOCAL INDEX ON {{ schema }}.customer (c_custkey);
ENFORCE LOCAL INDEX ON {{ schema }}.customer (c_nationkey);
ENFORCE LOCAL INDEX ON {{ schema }}.part (p_partkey);
ENFORCE LOCAL INDEX ON {{ schema }}.partsupp (ps_partkey, ps_suppkey);
ENFORCE LOCAL INDEX ON {{ schema }}.partsupp (ps_partkey);
ENFORCE LOCAL INDEX ON {{ schema }}.partsupp (ps_suppkey);
ENFORCE LOCAL INDEX ON {{ schema }}.orders (o_orderkey);
ENFORCE LOCAL INDEX ON {{ schema }}.orders (o_custkey);

COMMIT;
{% elif system_kind == 'clickhouse' %}
-- ClickHouse uses primary keys defined in table creation (ORDER BY clause)
-- The MergeTree ORDER BY clauses provide basic indexing
-- Additional skip indexes improve performance for specific query patterns

-- Q21: Multiple self-joins on lineitem by l_orderkey
-- Bloom filter index for fast IN/NOT IN subqueries
ALTER TABLE {{ schema }}.lineitem
    ADD INDEX IF NOT EXISTS idx_l_orderkey_bloom l_orderkey TYPE bloom_filter GRANULARITY 4;

-- Q21: Filtering by l_receiptdate > l_commitdate
-- MinMax index for date range comparisons
ALTER TABLE {{ schema }}.lineitem
    ADD INDEX IF NOT EXISTS idx_l_dates_minmax (l_receiptdate, l_commitdate) TYPE minmax GRANULARITY 4;

-- Q17: Correlated subquery on l_partkey
-- Set index for efficient l_partkey lookups
ALTER TABLE {{ schema }}.lineitem
    ADD INDEX IF NOT EXISTS idx_l_partkey_set l_partkey TYPE set(0) GRANULARITY 4;

-- Q17: MinMax index for l_quantity range checks (bloom_filter doesn't support Decimal)
ALTER TABLE {{ schema }}.lineitem
    ADD INDEX IF NOT EXISTS idx_l_quantity_minmax l_quantity TYPE minmax GRANULARITY 4;

-- Q08: Filter on p_type (highly selective)
ALTER TABLE {{ schema }}.part
    ADD INDEX IF NOT EXISTS idx_p_type_set p_type TYPE set(100) GRANULARITY 4;

-- Q17: Filter on p_brand and p_container
ALTER TABLE {{ schema }}.part
    ADD INDEX IF NOT EXISTS idx_p_brand_set p_brand TYPE set(50) GRANULARITY 4;
ALTER TABLE {{ schema }}.part
    ADD INDEX IF NOT EXISTS idx_p_container_set p_container TYPE set(50) GRANULARITY 4;

-- Q21: Filter on o_orderstatus (very low cardinality)
ALTER TABLE {{ schema }}.orders
    ADD INDEX IF NOT EXISTS idx_o_orderstatus_set o_orderstatus TYPE set(3) GRANULARITY 4;

-- Q08: Filter on n_name (Q21 also uses this)
ALTER TABLE {{ schema }}.nation
    ADD INDEX IF NOT EXISTS idx_n_name_bloom n_name TYPE bloom_filter GRANULARITY 1;

-- Q08: Filter on r_name
ALTER TABLE {{ schema }}.region
    ADD INDEX IF NOT EXISTS idx_r_name_set r_name TYPE set(10) GRANULARITY 1;

SELECT 'ClickHouse skip indexes created successfully';
{% else %}
{{ UNSUPPORTED_SYSTEM_KIND_ERROR_FOR[system_kind] }}
{% endif %}
