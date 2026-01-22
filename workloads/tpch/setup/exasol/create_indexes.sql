-- Exasol TPC-H Index Creation
-- Creates indexes to optimize query performance

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
