-- TPC-H Table Analysis Script
-- Analyzes tables and updates statistics for optimal query performance

{% if system_kind == 'exasol' %}
-- Analyze database to estimate statistics for query optimization
ANALYZE DATABASE ESTIMATE STATISTICS;
COMMIT;
{% elif system_kind == 'clickhouse' %}
-- ClickHouse Table Optimization
{% if system_extra.get('allow_statistics_optimize', 0) == 1 %}
-- Statistics are enabled - collect statistics for query optimizer (ClickHouse 24.6+)
-- Statistics help the query optimizer make better join order decisions

-- Add statistics for join optimization (most critical columns)

-- Lineitem: Most critical table for complex queries
ALTER TABLE {{ schema }}.lineitem ADD STATISTICS IF NOT EXISTS l_orderkey TYPE countmin, tdigest, uniq;
ALTER TABLE {{ schema }}.lineitem ADD STATISTICS IF NOT EXISTS l_partkey TYPE countmin, tdigest, uniq;
ALTER TABLE {{ schema }}.lineitem ADD STATISTICS IF NOT EXISTS l_suppkey TYPE countmin, tdigest, uniq;
ALTER TABLE {{ schema }}.lineitem ADD STATISTICS IF NOT EXISTS l_quantity TYPE countmin, tdigest;
ALTER TABLE {{ schema }}.lineitem ADD STATISTICS IF NOT EXISTS l_receiptdate TYPE countmin;
ALTER TABLE {{ schema }}.lineitem ADD STATISTICS IF NOT EXISTS l_commitdate TYPE countmin;

-- Orders: Critical for joins
ALTER TABLE {{ schema }}.orders ADD STATISTICS IF NOT EXISTS o_orderkey TYPE countmin, tdigest, uniq;
ALTER TABLE {{ schema }}.orders ADD STATISTICS IF NOT EXISTS o_custkey TYPE countmin, tdigest, uniq;
ALTER TABLE {{ schema }}.orders ADD STATISTICS IF NOT EXISTS o_orderdate TYPE countmin, tdigest;
ALTER TABLE {{ schema }}.orders ADD STATISTICS IF NOT EXISTS o_orderstatus TYPE countmin, uniq;

-- Part: Used in filtered joins
ALTER TABLE {{ schema }}.part ADD STATISTICS IF NOT EXISTS p_partkey TYPE countmin, tdigest, uniq;
ALTER TABLE {{ schema }}.part ADD STATISTICS IF NOT EXISTS p_type TYPE countmin, uniq;
ALTER TABLE {{ schema }}.part ADD STATISTICS IF NOT EXISTS p_brand TYPE countmin, uniq;
ALTER TABLE {{ schema }}.part ADD STATISTICS IF NOT EXISTS p_container TYPE countmin, uniq;

-- Supplier: Join and filter columns
ALTER TABLE {{ schema }}.supplier ADD STATISTICS IF NOT EXISTS s_suppkey TYPE countmin, tdigest, uniq;
ALTER TABLE {{ schema }}.supplier ADD STATISTICS IF NOT EXISTS s_nationkey TYPE countmin, tdigest, uniq;

-- Customer: Join columns
ALTER TABLE {{ schema }}.customer ADD STATISTICS IF NOT EXISTS c_custkey TYPE countmin, tdigest, uniq;
ALTER TABLE {{ schema }}.customer ADD STATISTICS IF NOT EXISTS c_nationkey TYPE countmin, tdigest, uniq;
ALTER TABLE {{ schema }}.customer ADD STATISTICS IF NOT EXISTS c_mktsegment TYPE countmin, uniq;

-- Partsupp: Join columns
ALTER TABLE {{ schema }}.partsupp ADD STATISTICS IF NOT EXISTS ps_partkey TYPE countmin, tdigest, uniq;
ALTER TABLE {{ schema }}.partsupp ADD STATISTICS IF NOT EXISTS ps_suppkey TYPE countmin, tdigest, uniq;

-- Nation: Small table but frequently joined
ALTER TABLE {{ schema }}.nation ADD STATISTICS IF NOT EXISTS n_nationkey TYPE countmin, tdigest, uniq;
ALTER TABLE {{ schema }}.nation ADD STATISTICS IF NOT EXISTS n_name TYPE countmin, uniq;
ALTER TABLE {{ schema }}.nation ADD STATISTICS IF NOT EXISTS n_regionkey TYPE countmin, tdigest, uniq;

-- Region: Small table
ALTER TABLE {{ schema }}.region ADD STATISTICS IF NOT EXISTS r_regionkey TYPE countmin, tdigest, uniq;
ALTER TABLE {{ schema }}.region ADD STATISTICS IF NOT EXISTS r_name TYPE countmin, uniq;

-- Materialize statistics
ALTER TABLE {{ schema }}.lineitem MATERIALIZE STATISTICS l_orderkey, l_partkey, l_suppkey, l_quantity, l_receiptdate, l_commitdate;
ALTER TABLE {{ schema }}.orders MATERIALIZE STATISTICS o_orderkey, o_custkey, o_orderdate, o_orderstatus;
ALTER TABLE {{ schema }}.part MATERIALIZE STATISTICS p_partkey, p_type, p_brand, p_container;
ALTER TABLE {{ schema }}.supplier MATERIALIZE STATISTICS s_suppkey, s_nationkey;
ALTER TABLE {{ schema }}.customer MATERIALIZE STATISTICS c_custkey, c_nationkey, c_mktsegment;
ALTER TABLE {{ schema }}.partsupp MATERIALIZE STATISTICS ps_partkey, ps_suppkey;
ALTER TABLE {{ schema }}.nation MATERIALIZE STATISTICS n_nationkey, n_name, n_regionkey;
ALTER TABLE {{ schema }}.region MATERIALIZE STATISTICS r_regionkey, r_name;
{% else %}
-- Statistics are disabled - using basic optimization only
{% endif %}

-- Optimize tables to merge data parts and improve compression
-- OPTIMIZE TABLE FINAL merges all data parts into a single optimized part
-- This improves query performance by reducing the number of parts to scan
{% if node_count > 1 %}
-- Multinode: OPTIMIZE only works on local MergeTree tables, not Distributed tables
OPTIMIZE TABLE {{ schema }}.nation_local ON CLUSTER '{cluster}' FINAL;
OPTIMIZE TABLE {{ schema }}.region_local ON CLUSTER '{cluster}' FINAL;
OPTIMIZE TABLE {{ schema }}.part_local ON CLUSTER '{cluster}' FINAL;
OPTIMIZE TABLE {{ schema }}.supplier_local ON CLUSTER '{cluster}' FINAL;
OPTIMIZE TABLE {{ schema }}.partsupp_local ON CLUSTER '{cluster}' FINAL;
OPTIMIZE TABLE {{ schema }}.customer_local ON CLUSTER '{cluster}' FINAL;
OPTIMIZE TABLE {{ schema }}.orders_local ON CLUSTER '{cluster}' FINAL;
OPTIMIZE TABLE {{ schema }}.lineitem_local ON CLUSTER '{cluster}' FINAL;
{% else %}
OPTIMIZE TABLE {{ schema }}.nation FINAL;
OPTIMIZE TABLE {{ schema }}.region FINAL;
OPTIMIZE TABLE {{ schema }}.part FINAL;
OPTIMIZE TABLE {{ schema }}.supplier FINAL;
OPTIMIZE TABLE {{ schema }}.partsupp FINAL;
OPTIMIZE TABLE {{ schema }}.customer FINAL;
OPTIMIZE TABLE {{ schema }}.orders FINAL;
OPTIMIZE TABLE {{ schema }}.lineitem FINAL;
{% endif %}

{% if system_extra.get('allow_statistics_optimize', 0) == 1 %}
SELECT 'ClickHouse statistics collected and tables optimized';
{% else %}
SELECT 'ClickHouse tables optimized (statistics disabled)';
{% endif %}
{% else %}
{{ UNSUPPORTED_SYSTEM_KIND_ERROR_FOR[system_kind] }}
{% endif %}
