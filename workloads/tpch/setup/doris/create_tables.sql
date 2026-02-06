-- Apache Doris TPC-H Table Creation
-- Uses OLAP engine with DUPLICATE KEY model for analytical queries
-- Optimizations applied:
--   - Colocate groups for local joins (lineitem_orders, part_partsupp)
--   - Date columns first in DUPLICATE KEY for range scan efficiency
--   - Tuned variant: Scale-aware bucket counts based on scale_factor

{# Calculate scale-aware buckets for tuned variant #}
{# IMPORTANT: Colocate group tables MUST have the same bucket count #}
{# - lineitem_orders group: lineitem + orders must match #}
{# - part_partsupp group: part + partsupp must match #}
{% if variant == 'tuned' %}
  {# Large tables: scale with data size, with reasonable bounds #}
  {# lineitem_orders colocate group - use same bucket count for both #}
  {% set lineitem_orders_buckets = [96, (scale_factor * 0.96)|int]|max %}
  {% if lineitem_orders_buckets > 192 %}{% set lineitem_orders_buckets = 192 %}{% endif %}
  {% set lineitem_buckets = lineitem_orders_buckets %}
  {% set orders_buckets = lineitem_orders_buckets %}
  {# part_partsupp colocate group - use same bucket count for both #}
  {% set part_partsupp_buckets = [24, (scale_factor * 0.24)|int]|max %}
  {% if part_partsupp_buckets > 48 %}{% set part_partsupp_buckets = 48 %}{% endif %}
  {% set partsupp_buckets = part_partsupp_buckets %}
  {% set part_buckets = part_partsupp_buckets %}
  {# Standalone tables #}
  {% set customer_buckets = [24, (scale_factor * 0.24)|int]|max %}
  {% if customer_buckets > 48 %}{% set customer_buckets = 48 %}{% endif %}
  {% set supplier_buckets = [12, (scale_factor * 0.12)|int]|max %}
  {% if supplier_buckets > 24 %}{% set supplier_buckets = 24 %}{% endif %}
{% else %}
  {# Official variant: use reasonable defaults #}
  {# lineitem_orders colocate group - MUST use same bucket count #}
  {% set lineitem_orders_buckets = bucket_count|default(16) %}
  {% set lineitem_buckets = lineitem_orders_buckets %}
  {% set orders_buckets = lineitem_orders_buckets %}
  {# part_partsupp colocate group - MUST use same bucket count #}
  {% set part_partsupp_buckets = bucket_count|default(8) %}
  {% set partsupp_buckets = part_partsupp_buckets %}
  {% set part_buckets = part_partsupp_buckets %}
  {# Standalone tables #}
  {% set customer_buckets = bucket_count|default(8) %}
  {% set supplier_buckets = bucket_count|default(4) %}
{% endif %}

{# Small reference tables always use 1 bucket #}
{% set nation_buckets = 1 %}
{% set region_buckets = 1 %}

-- Reference tables (tiny, no colocate needed)

CREATE TABLE IF NOT EXISTS {{ schema }}.nation (
    n_nationkey INT NOT NULL,
    n_name VARCHAR(25) NOT NULL,
    n_regionkey INT NOT NULL,
    n_comment VARCHAR(152)
)
ENGINE=OLAP
DUPLICATE KEY(n_nationkey)
DISTRIBUTED BY HASH(n_nationkey) BUCKETS {{ nation_buckets }}
PROPERTIES ("replication_num" = "{{ replication_num|default(1) }}");

CREATE TABLE IF NOT EXISTS {{ schema }}.region (
    r_regionkey INT NOT NULL,
    r_name VARCHAR(25) NOT NULL,
    r_comment VARCHAR(152)
)
ENGINE=OLAP
DUPLICATE KEY(r_regionkey)
DISTRIBUTED BY HASH(r_regionkey) BUCKETS {{ region_buckets }}
PROPERTIES ("replication_num" = "{{ replication_num|default(1) }}");

-- Part and partsupp tables (colocate on partkey)

CREATE TABLE IF NOT EXISTS {{ schema }}.part (
    p_partkey INT NOT NULL,
    p_name VARCHAR(55) NOT NULL,
    p_mfgr VARCHAR(25) NOT NULL,
    p_brand VARCHAR(10) NOT NULL,
    p_type VARCHAR(25) NOT NULL,
    p_size INT NOT NULL,
    p_container VARCHAR(10) NOT NULL,
    p_retailprice DECIMAL(15,2) NOT NULL,
    p_comment VARCHAR(23) NOT NULL
)
ENGINE=OLAP
DUPLICATE KEY(p_partkey)
DISTRIBUTED BY HASH(p_partkey) BUCKETS {{ part_buckets }}
PROPERTIES (
    "replication_num" = "{{ replication_num|default(1) }}",
    "colocate_with" = "part_partsupp"
);

CREATE TABLE IF NOT EXISTS {{ schema }}.partsupp (
    ps_partkey INT NOT NULL,
    ps_suppkey INT NOT NULL,
    ps_availqty INT NOT NULL,
    ps_supplycost DECIMAL(15,2) NOT NULL,
    ps_comment VARCHAR(199) NOT NULL
)
ENGINE=OLAP
DUPLICATE KEY(ps_partkey, ps_suppkey)
DISTRIBUTED BY HASH(ps_partkey) BUCKETS {{ partsupp_buckets }}
PROPERTIES (
    "replication_num" = "{{ replication_num|default(1) }}",
    "colocate_with" = "part_partsupp"
);

-- Supplier table (standalone, joins to nation)

CREATE TABLE IF NOT EXISTS {{ schema }}.supplier (
    s_suppkey INT NOT NULL,
    s_name VARCHAR(25) NOT NULL,
    s_address VARCHAR(40) NOT NULL,
    s_nationkey INT NOT NULL,
    s_phone VARCHAR(15) NOT NULL,
    s_acctbal DECIMAL(15,2) NOT NULL,
    s_comment VARCHAR(101) NOT NULL
)
ENGINE=OLAP
DUPLICATE KEY(s_suppkey)
DISTRIBUTED BY HASH(s_suppkey) BUCKETS {{ supplier_buckets }}
PROPERTIES ("replication_num" = "{{ replication_num|default(1) }}");

-- Customer table (standalone, joins to nation and orders)

CREATE TABLE IF NOT EXISTS {{ schema }}.customer (
    c_custkey INT NOT NULL,
    c_name VARCHAR(25) NOT NULL,
    c_address VARCHAR(40) NOT NULL,
    c_nationkey INT NOT NULL,
    c_phone VARCHAR(15) NOT NULL,
    c_acctbal DECIMAL(15,2) NOT NULL,
    c_mktsegment VARCHAR(10) NOT NULL,
    c_comment VARCHAR(117) NOT NULL
)
ENGINE=OLAP
DUPLICATE KEY(c_custkey)
DISTRIBUTED BY HASH(c_custkey) BUCKETS {{ customer_buckets }}
PROPERTIES ("replication_num" = "{{ replication_num|default(1) }}");

-- Orders and lineitem tables (colocate on orderkey for efficient joins)
-- Date columns first in DUPLICATE KEY for range scan efficiency

CREATE TABLE IF NOT EXISTS {{ schema }}.orders (
    o_orderdate DATE NOT NULL,
    o_orderkey BIGINT NOT NULL,
    o_custkey INT NOT NULL,
    o_orderstatus VARCHAR(1) NOT NULL,
    o_totalprice DECIMAL(15,2) NOT NULL,
    o_orderpriority VARCHAR(15) NOT NULL,
    o_clerk VARCHAR(15) NOT NULL,
    o_shippriority INT NOT NULL,
    o_comment VARCHAR(79) NOT NULL
)
ENGINE=OLAP
DUPLICATE KEY(o_orderdate, o_orderkey)
DISTRIBUTED BY HASH(o_orderkey) BUCKETS {{ orders_buckets }}
PROPERTIES (
    "replication_num" = "{{ replication_num|default(1) }}",
    "colocate_with" = "lineitem_orders"
);

CREATE TABLE IF NOT EXISTS {{ schema }}.lineitem (
    l_shipdate DATE NOT NULL,
    l_orderkey BIGINT NOT NULL,
    l_partkey INT NOT NULL,
    l_suppkey INT NOT NULL,
    l_linenumber INT NOT NULL,
    l_quantity DECIMAL(15,2) NOT NULL,
    l_extendedprice DECIMAL(15,2) NOT NULL,
    l_discount DECIMAL(15,2) NOT NULL,
    l_tax DECIMAL(15,2) NOT NULL,
    l_returnflag VARCHAR(1) NOT NULL,
    l_linestatus VARCHAR(1) NOT NULL,
    l_commitdate DATE NOT NULL,
    l_receiptdate DATE NOT NULL,
    l_shipinstruct VARCHAR(25) NOT NULL,
    l_shipmode VARCHAR(10) NOT NULL,
    l_comment VARCHAR(44) NOT NULL
)
ENGINE=OLAP
DUPLICATE KEY(l_shipdate, l_orderkey)
DISTRIBUTED BY HASH(l_orderkey) BUCKETS {{ lineitem_buckets }}
PROPERTIES (
    "replication_num" = "{{ replication_num|default(1) }}",
    "colocate_with" = "lineitem_orders"
);
