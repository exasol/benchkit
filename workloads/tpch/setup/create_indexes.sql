-- TPC-H Index Creation Script
-- Creates indexes to optimize query performance for both database systems

{% if system_kind == 'exasol' %}
{% if node_count > 1 %}
-- MULTINODE CLUSTER: Create indices optimized for distributed execution
-- Mix of LOCAL indices (intra-node performance) and GLOBAL indices (cross-node joins)

-- Lineitem: Mix of local and global indices for distributed joins
ENFORCE LOCAL INDEX ON {{ schema }}.lineitem (l_suppkey);
ENFORCE GLOBAL INDEX ON {{ schema }}.lineitem (l_partkey, l_suppkey);
ENFORCE GLOBAL INDEX ON {{ schema }}.lineitem (l_partkey);
ENFORCE LOCAL INDEX ON {{ schema }}.lineitem (l_orderkey);

-- Dimension tables: Regular indices (replicated across nodes)
ENFORCE INDEX ON {{ schema }}.nation (n_nationkey);
ENFORCE INDEX ON {{ schema }}.region (r_regionkey);
ENFORCE INDEX ON {{ schema }}.supplier (s_suppkey);
ENFORCE INDEX ON {{ schema }}.supplier (s_nationkey);

-- Large fact tables: Local indices for intra-node performance
ENFORCE LOCAL INDEX ON {{ schema }}.customer (c_custkey);
ENFORCE LOCAL INDEX ON {{ schema }}.customer (c_nationkey);
ENFORCE LOCAL INDEX ON {{ schema }}.part (p_partkey);
ENFORCE LOCAL INDEX ON {{ schema }}.partsupp (ps_partkey, ps_suppkey);
ENFORCE LOCAL INDEX ON {{ schema }}.partsupp (ps_partkey);
ENFORCE LOCAL INDEX ON {{ schema }}.partsupp (ps_suppkey);

-- Orders: Both local and global for distributed queries
ENFORCE LOCAL INDEX ON {{ schema }}.orders (o_orderkey);
ENFORCE GLOBAL INDEX ON {{ schema }}.orders (o_orderkey);
ENFORCE LOCAL INDEX ON {{ schema }}.orders (o_custkey);

COMMIT;
{% else %}
-- Single node: Create local indexes for Exasol
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
{% endif %}
{% elif system_kind == 'clickhouse' %}
-- ClickHouse Skip Indexes: DISABLED for TPC-H Analytical Workload
--
-- Analysis showed that skip indexes cause net performance REGRESSION for TPC-H:
-- - 15/22 queries became slower (1-7% regression)
-- - Only 2/22 queries improved (Q20: -9.5%, Q12: -1.3%)
-- - Overall net negative impact on workload
--
-- Root causes:
-- 1. Redundancy: Many skip indexes duplicate MergeTree primary key (ORDER BY)
--    Example: l_orderkey bloom_filter is redundant with ORDER BY (l_shipdate, l_orderkey, l_partkey)
-- 2. Low selectivity: Indexes on low-cardinality columns (o_orderstatus: 3 values) add overhead
-- 3. Workload mismatch: TPC-H = analytical scans; skip indexes = OLTP point queries
-- 4. Granularity overhead: GRANULARITY 4 adds index maintenance cost without benefit
--
-- Decision: Rely on MergeTree primary keys and OPTIMIZE TABLE compression for best performance
-- For analytical workloads, well-designed ORDER BY clauses are more effective than skip indexes

SELECT 'ClickHouse indexing: Using MergeTree primary keys only (skip indexes disabled for analytical workload)';
{% elif system_kind == 'trino' %}
-- Trino/Hive: No traditional indexes supported
-- Hive connector uses columnar storage formats (ORC/Parquet) for efficient data access
-- Performance optimizations come from:
-- 1. Columnar storage format (reads only needed columns)
-- 2. Predicate pushdown (filters applied at storage layer)
-- 3. Partition pruning (if tables are partitioned)

SELECT 'Trino: No indexes needed (using columnar storage for efficient data access)';
{% else %}
{{ UNSUPPORTED_SYSTEM_KIND_ERROR_FOR[system_kind] }}
{% endif %}
