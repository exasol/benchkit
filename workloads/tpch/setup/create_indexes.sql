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
-- Additional indexes are not typically needed for TPC-H queries in ClickHouse
-- The MergeTree ORDER BY clauses provide the necessary indexing:
--   - nation: ORDER BY n_nationkey
--   - region: ORDER BY r_regionkey
--   - part: ORDER BY p_partkey
--   - supplier: ORDER BY s_suppkey
--   - partsupp: ORDER BY ps_partkey
--   - customer: ORDER BY c_custkey
--   - orders: ORDER BY o_orderkey
--   - lineitem: ORDER BY l_orderkey

-- No additional indexes needed for ClickHouse
SELECT 'ClickHouse indexes created via ORDER BY clauses in table definitions';
{% else %}
{{ UNSUPPORTED_SYSTEM_KIND_ERROR_FOR[system_kind] }}
{% endif %}
