-- TPC-H Table Creation Script
-- Creates all 8 TPC-H tables with appropriate data types and storage options for each database system

{% if system_kind == 'exasol' %}
-- Exasol table creation
{% elif system_kind == 'clickhouse' %}
-- ClickHouse table creation
{% if node_count > 1 %}
-- MULTINODE CLUSTER: Creating local tables on all nodes + distributed tables
{% else %}
-- Single node setup
{% endif %}
{% elif system_kind == 'trino' %}
-- Trino table creation using external Parquet tables
-- Data is read directly from Parquet files - zero copy loading
-- External location from storage backend (S3 or local): {{ data_locations.nation | default('not-set') }}
{% else %}
{{ UNSUPPORTED_SYSTEM_KIND_ERROR_FOR[system_kind] }}
{% endif %}

-- Nation table
{% if system_kind == 'exasol' %}
CREATE OR REPLACE TABLE {{ schema }}.nation (
    n_nationkey DEC(11),
    n_name CHAR(25) CHARACTER SET ASCII,
    n_regionkey DEC(11),
    n_comment VARCHAR(152) CHARACTER SET ASCII
);
{% elif system_kind == 'clickhouse' %}
{% if node_count > 1 %}
CREATE TABLE IF NOT EXISTS {{ schema }}.nation_local ON CLUSTER '{cluster}' (
    n_nationkey INTEGER NOT NULL,
    n_name CHAR(25) NOT NULL,
    n_regionkey INTEGER NOT NULL,
    n_comment VARCHAR(152)
) ENGINE MergeTree() ORDER BY n_nationkey;
{% else %}
CREATE OR REPLACE TABLE {{ schema }}.nation (
    n_nationkey INTEGER NOT NULL,
    n_name CHAR(25) NOT NULL,
    n_regionkey INTEGER NOT NULL,
    n_comment VARCHAR(152)
) ENGINE MergeTree() ORDER BY n_nationkey;
{% endif %}
{% elif system_kind == 'trino' %}
CREATE TABLE IF NOT EXISTS {{ schema }}.nation (
    n_nationkey INTEGER,
    n_name VARCHAR(25),
    n_regionkey INTEGER,
    n_comment VARCHAR(152)
)
WITH (
    format = 'PARQUET',
    external_location = '{{ data_locations.nation }}'
);
{% endif %}

-- Region table
{% if system_kind == 'exasol' %}
CREATE OR REPLACE TABLE {{ schema }}.region (
    r_regionkey DEC(11),
    r_name CHAR(25) CHARACTER SET ASCII,
    r_comment VARCHAR(152) CHARACTER SET ASCII
);
{% elif system_kind == 'clickhouse' %}
{% if node_count > 1 %}
CREATE TABLE IF NOT EXISTS {{ schema }}.region_local ON CLUSTER '{cluster}' (
    r_regionkey INTEGER NOT NULL,
    r_name CHAR(25) NOT NULL,
    r_comment VARCHAR(152)
) ENGINE MergeTree() ORDER BY r_regionkey;
{% else %}
CREATE OR REPLACE TABLE {{ schema }}.region (
    r_regionkey INTEGER NOT NULL,
    r_name CHAR(25) NOT NULL,
    r_comment VARCHAR(152)
) ENGINE MergeTree() ORDER BY r_regionkey;
{% endif %}
{% elif system_kind == 'trino' %}
CREATE TABLE IF NOT EXISTS {{ schema }}.region (
    r_regionkey INTEGER,
    r_name VARCHAR(25),
    r_comment VARCHAR(152)
)
WITH (
    format = 'PARQUET',
    external_location = '{{ data_locations.region }}'
);
{% endif %}

-- Part table
{% if system_kind == 'exasol' %}
CREATE OR REPLACE TABLE {{ schema }}.part (
    p_partkey DEC(11),
    p_name VARCHAR(55) CHARACTER SET ASCII,
    p_mfgr CHAR(25) CHARACTER SET ASCII,
    p_brand CHAR(10) CHARACTER SET ASCII,
    p_type VARCHAR(25) CHARACTER SET ASCII,
    p_size DEC(10),
    p_container CHAR(10) CHARACTER SET ASCII,
    p_retailprice DECIMAL(12,2),
    p_comment VARCHAR(23) CHARACTER SET ASCII,
    DISTRIBUTE BY p_partkey
);
{% elif system_kind == 'clickhouse' %}
{% if node_count > 1 %}
CREATE TABLE IF NOT EXISTS {{ schema }}.part_local ON CLUSTER '{cluster}' (
    p_partkey INTEGER NOT NULL,
    p_name VARCHAR(55) NOT NULL,
    p_mfgr CHAR(25) NOT NULL,
    p_brand CHAR(10) NOT NULL,
    p_type VARCHAR(25) NOT NULL,
    p_size INTEGER NOT NULL,
    p_container CHAR(10) NOT NULL,
    p_retailprice DECIMAL(15,2) NOT NULL,
    p_comment VARCHAR(23) NOT NULL
) ENGINE MergeTree() ORDER BY p_partkey;
{% else %}
CREATE OR REPLACE TABLE {{ schema }}.part (
    p_partkey INTEGER NOT NULL,
    p_name VARCHAR(55) NOT NULL,
    p_mfgr CHAR(25) NOT NULL,
    p_brand CHAR(10) NOT NULL,
    p_type VARCHAR(25) NOT NULL,
    p_size INTEGER NOT NULL,
    p_container CHAR(10) NOT NULL,
    p_retailprice DECIMAL(15,2) NOT NULL,
    p_comment VARCHAR(23) NOT NULL
) ENGINE MergeTree() ORDER BY p_partkey;
{% endif %}
{% elif system_kind == 'trino' %}
CREATE TABLE IF NOT EXISTS {{ schema }}.part (
    p_partkey INTEGER,
    p_name VARCHAR(55),
    p_mfgr VARCHAR(25),
    p_brand VARCHAR(10),
    p_type VARCHAR(25),
    p_size INTEGER,
    p_container VARCHAR(10),
    p_retailprice DECIMAL(15,2),
    p_comment VARCHAR(23)
)
WITH (
    format = 'PARQUET',
    external_location = '{{ data_locations.part }}'
);
{% endif %}

-- Supplier table
{% if system_kind == 'exasol' %}
CREATE OR REPLACE TABLE {{ schema }}.supplier (
    s_suppkey DEC(11),
    s_name CHAR(25) CHARACTER SET ASCII,
    s_address VARCHAR(40) CHARACTER SET ASCII,
    s_nationkey DEC(11),
    s_phone CHAR(15) CHARACTER SET ASCII,
    s_acctbal DECIMAL(12,2),
    s_comment VARCHAR(101) CHARACTER SET ASCII,
    DISTRIBUTE BY s_suppkey
);
{% elif system_kind == 'clickhouse' %}
{% if node_count > 1 %}
CREATE TABLE IF NOT EXISTS {{ schema }}.supplier_local ON CLUSTER '{cluster}' (
    s_suppkey INTEGER NOT NULL,
    s_name CHAR(25) NOT NULL,
    s_address VARCHAR(40) NOT NULL,
    s_nationkey INTEGER NOT NULL,
    s_phone CHAR(15) NOT NULL,
    s_acctbal DECIMAL(15,2) NOT NULL,
    s_comment VARCHAR(101) NOT NULL
) ENGINE MergeTree() ORDER BY s_suppkey;
{% else %}
CREATE OR REPLACE TABLE {{ schema }}.supplier (
    s_suppkey INTEGER NOT NULL,
    s_name CHAR(25) NOT NULL,
    s_address VARCHAR(40) NOT NULL,
    s_nationkey INTEGER NOT NULL,
    s_phone CHAR(15) NOT NULL,
    s_acctbal DECIMAL(15,2) NOT NULL,
    s_comment VARCHAR(101) NOT NULL
) ENGINE MergeTree() ORDER BY s_suppkey;
{% endif %}
{% elif system_kind == 'trino' %}
CREATE TABLE IF NOT EXISTS {{ schema }}.supplier (
    s_suppkey INTEGER,
    s_name VARCHAR(25),
    s_address VARCHAR(40),
    s_nationkey INTEGER,
    s_phone VARCHAR(15),
    s_acctbal DECIMAL(15,2),
    s_comment VARCHAR(101)
)
WITH (
    format = 'PARQUET',
    external_location = '{{ data_locations.supplier }}'
);
{% endif %}

-- Partsupp table
{% if system_kind == 'exasol' %}
CREATE OR REPLACE TABLE {{ schema }}.partsupp (
    ps_partkey DEC(11),
    ps_suppkey DEC(11),
    ps_availqty DEC(10),
    ps_supplycost DECIMAL(12,2),
    ps_comment VARCHAR(199) CHARACTER SET ASCII,
    DISTRIBUTE BY ps_partkey
);
{% elif system_kind == 'clickhouse' %}
{% if node_count > 1 %}
CREATE TABLE IF NOT EXISTS {{ schema }}.partsupp_local ON CLUSTER '{cluster}' (
    ps_partkey INTEGER NOT NULL,
    ps_suppkey INTEGER NOT NULL,
    ps_availqty INTEGER NOT NULL,
    ps_supplycost DECIMAL(15,2) NOT NULL,
    ps_comment VARCHAR(199) NOT NULL
) ENGINE MergeTree() ORDER BY (ps_partkey, ps_suppkey);
{% else %}
CREATE OR REPLACE TABLE {{ schema }}.partsupp (
    ps_partkey INTEGER NOT NULL,
    ps_suppkey INTEGER NOT NULL,
    ps_availqty INTEGER NOT NULL,
    ps_supplycost DECIMAL(15,2) NOT NULL,
    ps_comment VARCHAR(199) NOT NULL
) ENGINE MergeTree() ORDER BY (ps_partkey, ps_suppkey);
{% endif %}
{% elif system_kind == 'trino' %}
CREATE TABLE IF NOT EXISTS {{ schema }}.partsupp (
    ps_partkey INTEGER,
    ps_suppkey INTEGER,
    ps_availqty INTEGER,
    ps_supplycost DECIMAL(15,2),
    ps_comment VARCHAR(199)
)
WITH (
    format = 'PARQUET',
    external_location = '{{ data_locations.partsupp }}'
);
{% endif %}

-- Customer table
{% if system_kind == 'exasol' %}
CREATE OR REPLACE TABLE {{ schema }}.customer (
    c_custkey DEC(11),
    c_name VARCHAR(25) CHARACTER SET ASCII,
    c_address VARCHAR(40) CHARACTER SET ASCII,
    c_nationkey DEC(11),
    c_phone CHAR(15) CHARACTER SET ASCII,
    c_acctbal DECIMAL(12,2),
    c_mktsegment CHAR(10) CHARACTER SET ASCII,
    c_comment VARCHAR(117) CHARACTER SET ASCII,
    DISTRIBUTE BY c_custkey
);
{% elif system_kind == 'clickhouse' %}
{% if node_count > 1 %}
CREATE TABLE IF NOT EXISTS {{ schema }}.customer_local ON CLUSTER '{cluster}' (
    c_custkey INTEGER NOT NULL,
    c_name VARCHAR(25) NOT NULL,
    c_address VARCHAR(40) NOT NULL,
    c_nationkey INTEGER NOT NULL,
    c_phone CHAR(15) NOT NULL,
    c_acctbal DECIMAL(15,2) NOT NULL,
    c_mktsegment CHAR(10) NOT NULL,
    c_comment VARCHAR(117) NOT NULL
) ENGINE MergeTree() ORDER BY (c_mktsegment, c_custkey);
{% else %}
CREATE OR REPLACE TABLE {{ schema }}.customer (
    c_custkey INTEGER NOT NULL,
    c_name VARCHAR(25) NOT NULL,
    c_address VARCHAR(40) NOT NULL,
    c_nationkey INTEGER NOT NULL,
    c_phone CHAR(15) NOT NULL,
    c_acctbal DECIMAL(15,2) NOT NULL,
    c_mktsegment CHAR(10) NOT NULL,
    c_comment VARCHAR(117) NOT NULL
) ENGINE MergeTree() ORDER BY (c_mktsegment, c_custkey);
{% endif %}
{% elif system_kind == 'trino' %}
CREATE TABLE IF NOT EXISTS {{ schema }}.customer (
    c_custkey INTEGER,
    c_name VARCHAR(25),
    c_address VARCHAR(40),
    c_nationkey INTEGER,
    c_phone VARCHAR(15),
    c_acctbal DECIMAL(15,2),
    c_mktsegment VARCHAR(10),
    c_comment VARCHAR(117)
)
WITH (
    format = 'PARQUET',
    external_location = '{{ data_locations.customer }}'
);
{% endif %}

-- Orders table
{% if system_kind == 'exasol' %}
CREATE OR REPLACE TABLE {{ schema }}.orders (
    o_orderkey DEC(12),
    o_custkey DEC(11),
    o_orderstatus CHAR(1) CHARACTER SET ASCII,
    o_totalprice DECIMAL(12,2),
    o_orderdate DATE,
    o_orderpriority CHAR(15) CHARACTER SET ASCII,
    o_clerk CHAR(15) CHARACTER SET ASCII,
    o_shippriority DEC(10),
    o_comment VARCHAR(79) CHARACTER SET ASCII,
    DISTRIBUTE BY o_custkey
);
{% elif system_kind == 'clickhouse' %}
{% if node_count > 1 %}
CREATE TABLE IF NOT EXISTS {{ schema }}.orders_local ON CLUSTER '{cluster}' (
    o_orderkey BIGINT NOT NULL,
    o_custkey INTEGER NOT NULL,
    o_orderstatus CHAR(1) NOT NULL,
    o_totalprice DECIMAL(15,2) NOT NULL,
    o_orderdate DATE NOT NULL,
    o_orderpriority CHAR(15) NOT NULL,
    o_clerk CHAR(15) NOT NULL,
    o_shippriority INTEGER NOT NULL,
    o_comment VARCHAR(79) NOT NULL
) ENGINE MergeTree() ORDER BY (o_orderdate, o_orderkey);
{% else %}
CREATE OR REPLACE TABLE {{ schema }}.orders (
    o_orderkey BIGINT NOT NULL,
    o_custkey INTEGER NOT NULL,
    o_orderstatus CHAR(1) NOT NULL,
    o_totalprice DECIMAL(15,2) NOT NULL,
    o_orderdate DATE NOT NULL,
    o_orderpriority CHAR(15) NOT NULL,
    o_clerk CHAR(15) NOT NULL,
    o_shippriority INTEGER NOT NULL,
    o_comment VARCHAR(79) NOT NULL
) ENGINE MergeTree() ORDER BY (o_orderdate, o_orderkey);
{% endif %}
{% elif system_kind == 'trino' %}
CREATE TABLE IF NOT EXISTS {{ schema }}.orders (
    o_orderkey BIGINT,
    o_custkey INTEGER,
    o_orderstatus VARCHAR(1),
    o_totalprice DECIMAL(15,2),
    o_orderdate DATE,
    o_orderpriority VARCHAR(15),
    o_clerk VARCHAR(15),
    o_shippriority INTEGER,
    o_comment VARCHAR(79)
)
WITH (
    format = 'PARQUET',
    external_location = '{{ data_locations.orders }}'
);
{% endif %}

-- Lineitem table
{% if system_kind == 'exasol' %}
CREATE OR REPLACE TABLE {{ schema }}.lineitem (
    l_orderkey DEC(12),
    l_partkey DEC(11),
    l_suppkey DEC(11),
    l_linenumber DEC(10),
    l_quantity DECIMAL(12,2),
    l_extendedprice DECIMAL(12,2),
    l_discount DECIMAL(12,2),
    l_tax DECIMAL(12,2),
    l_returnflag CHAR(1) CHARACTER SET ASCII,
    l_linestatus CHAR(1) CHARACTER SET ASCII,
    l_shipdate DATE,
    l_commitdate DATE,
    l_receiptdate DATE,
    l_shipinstruct CHAR(25) CHARACTER SET ASCII,
    l_shipmode CHAR(10) CHARACTER SET ASCII,
    l_comment VARCHAR(44) CHARACTER SET ASCII,
    DISTRIBUTE BY l_orderkey
);
{% elif system_kind == 'clickhouse' %}
{% if node_count > 1 %}
CREATE TABLE IF NOT EXISTS {{ schema }}.lineitem_local ON CLUSTER '{cluster}' (
    l_orderkey BIGINT NOT NULL,
    l_partkey INTEGER NOT NULL,
    l_suppkey INTEGER NOT NULL,
    l_linenumber INTEGER NOT NULL,
    l_quantity DECIMAL(15,2) NOT NULL,
    l_extendedprice DECIMAL(15,2) NOT NULL,
    l_discount DECIMAL(15,2) NOT NULL,
    l_tax DECIMAL(15,2) NOT NULL,
    l_returnflag CHAR(1) NOT NULL,
    l_linestatus CHAR(1) NOT NULL,
    l_shipdate DATE NOT NULL,
    l_commitdate DATE NOT NULL,
    l_receiptdate DATE NOT NULL,
    l_shipinstruct CHAR(25) NOT NULL,
    l_shipmode CHAR(10) NOT NULL,
    l_comment VARCHAR(44) NOT NULL
) ENGINE MergeTree() ORDER BY (l_shipdate, l_orderkey, l_partkey);
{% else %}
CREATE OR REPLACE TABLE {{ schema }}.lineitem (
    l_orderkey BIGINT NOT NULL,
    l_partkey INTEGER NOT NULL,
    l_suppkey INTEGER NOT NULL,
    l_linenumber INTEGER NOT NULL,
    l_quantity DECIMAL(15,2) NOT NULL,
    l_extendedprice DECIMAL(15,2) NOT NULL,
    l_discount DECIMAL(15,2) NOT NULL,
    l_tax DECIMAL(15,2) NOT NULL,
    l_returnflag CHAR(1) NOT NULL,
    l_linestatus CHAR(1) NOT NULL,
    l_shipdate DATE NOT NULL,
    l_commitdate DATE NOT NULL,
    l_receiptdate DATE NOT NULL,
    l_shipinstruct CHAR(25) NOT NULL,
    l_shipmode CHAR(10) NOT NULL,
    l_comment VARCHAR(44) NOT NULL
) ENGINE MergeTree() ORDER BY (l_shipdate, l_orderkey, l_partkey);
{% endif %}
{% elif system_kind == 'trino' %}
CREATE TABLE IF NOT EXISTS {{ schema }}.lineitem (
    l_orderkey BIGINT,
    l_partkey INTEGER,
    l_suppkey INTEGER,
    l_linenumber INTEGER,
    l_quantity DECIMAL(15,2),
    l_extendedprice DECIMAL(15,2),
    l_discount DECIMAL(15,2),
    l_tax DECIMAL(15,2),
    l_returnflag VARCHAR(1),
    l_linestatus VARCHAR(1),
    l_shipdate DATE,
    l_commitdate DATE,
    l_receiptdate DATE,
    l_shipinstruct VARCHAR(25),
    l_shipmode VARCHAR(10),
    l_comment VARCHAR(44)
)
WITH (
    format = 'PARQUET',
    external_location = '{{ data_locations.lineitem }}'
);
{% endif %}

{% if system_kind == 'clickhouse' and node_count > 1 %}
-- Create Distributed tables for multinode cluster
-- These provide a unified interface to query sharded data across all nodes

CREATE TABLE IF NOT EXISTS {{ schema }}.nation ON CLUSTER '{cluster}' AS {{ schema }}.nation_local
ENGINE = Distributed('{cluster}', currentDatabase(), nation_local, rand());

CREATE TABLE IF NOT EXISTS {{ schema }}.region ON CLUSTER '{cluster}' AS {{ schema }}.region_local
ENGINE = Distributed('{cluster}', currentDatabase(), region_local, rand());

CREATE TABLE IF NOT EXISTS {{ schema }}.part ON CLUSTER '{cluster}' AS {{ schema }}.part_local
ENGINE = Distributed('{cluster}', currentDatabase(), part_local, rand());

CREATE TABLE IF NOT EXISTS {{ schema }}.supplier ON CLUSTER '{cluster}' AS {{ schema }}.supplier_local
ENGINE = Distributed('{cluster}', currentDatabase(), supplier_local, rand());

CREATE TABLE IF NOT EXISTS {{ schema }}.partsupp ON CLUSTER '{cluster}' AS {{ schema }}.partsupp_local
ENGINE = Distributed('{cluster}', currentDatabase(), partsupp_local, rand());

CREATE TABLE IF NOT EXISTS {{ schema }}.customer ON CLUSTER '{cluster}' AS {{ schema }}.customer_local
ENGINE = Distributed('{cluster}', currentDatabase(), customer_local, rand());

CREATE TABLE IF NOT EXISTS {{ schema }}.orders ON CLUSTER '{cluster}' AS {{ schema }}.orders_local
ENGINE = Distributed('{cluster}', currentDatabase(), orders_local, rand());

CREATE TABLE IF NOT EXISTS {{ schema }}.lineitem ON CLUSTER '{cluster}' AS {{ schema }}.lineitem_local
ENGINE = Distributed('{cluster}', currentDatabase(), lineitem_local, rand());
{% endif %}
