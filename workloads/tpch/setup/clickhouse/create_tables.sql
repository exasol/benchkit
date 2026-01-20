-- ClickHouse TPC-H Table Creation
-- Creates all 8 TPC-H tables with ClickHouse-specific types and MergeTree engines
-- Supports both single-node and multinode cluster configurations

{% if node_count > 1 %}
-- MULTINODE CLUSTER: Creating local tables on all nodes + distributed tables

-- Nation table (local)
CREATE TABLE IF NOT EXISTS {{ schema }}.nation_local ON CLUSTER '{cluster}' (
    n_nationkey INTEGER NOT NULL,
    n_name CHAR(25) NOT NULL,
    n_regionkey INTEGER NOT NULL,
    n_comment VARCHAR(152)
) ENGINE MergeTree() ORDER BY n_nationkey;

-- Region table (local)
CREATE TABLE IF NOT EXISTS {{ schema }}.region_local ON CLUSTER '{cluster}' (
    r_regionkey INTEGER NOT NULL,
    r_name CHAR(25) NOT NULL,
    r_comment VARCHAR(152)
) ENGINE MergeTree() ORDER BY r_regionkey;

-- Part table (local)
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

-- Supplier table (local)
CREATE TABLE IF NOT EXISTS {{ schema }}.supplier_local ON CLUSTER '{cluster}' (
    s_suppkey INTEGER NOT NULL,
    s_name CHAR(25) NOT NULL,
    s_address VARCHAR(40) NOT NULL,
    s_nationkey INTEGER NOT NULL,
    s_phone CHAR(15) NOT NULL,
    s_acctbal DECIMAL(15,2) NOT NULL,
    s_comment VARCHAR(101) NOT NULL
) ENGINE MergeTree() ORDER BY s_suppkey;

-- Partsupp table (local)
CREATE TABLE IF NOT EXISTS {{ schema }}.partsupp_local ON CLUSTER '{cluster}' (
    ps_partkey INTEGER NOT NULL,
    ps_suppkey INTEGER NOT NULL,
    ps_availqty INTEGER NOT NULL,
    ps_supplycost DECIMAL(15,2) NOT NULL,
    ps_comment VARCHAR(199) NOT NULL
) ENGINE MergeTree() ORDER BY (ps_partkey, ps_suppkey);

-- Customer table (local)
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

-- Orders table (local)
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

-- Lineitem table (local)
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

{% else %}
-- Single node setup

-- Nation table
CREATE OR REPLACE TABLE {{ schema }}.nation (
    n_nationkey INTEGER NOT NULL,
    n_name CHAR(25) NOT NULL,
    n_regionkey INTEGER NOT NULL,
    n_comment VARCHAR(152)
) ENGINE MergeTree() ORDER BY n_nationkey;

-- Region table
CREATE OR REPLACE TABLE {{ schema }}.region (
    r_regionkey INTEGER NOT NULL,
    r_name CHAR(25) NOT NULL,
    r_comment VARCHAR(152)
) ENGINE MergeTree() ORDER BY r_regionkey;

-- Part table
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

-- Supplier table
CREATE OR REPLACE TABLE {{ schema }}.supplier (
    s_suppkey INTEGER NOT NULL,
    s_name CHAR(25) NOT NULL,
    s_address VARCHAR(40) NOT NULL,
    s_nationkey INTEGER NOT NULL,
    s_phone CHAR(15) NOT NULL,
    s_acctbal DECIMAL(15,2) NOT NULL,
    s_comment VARCHAR(101) NOT NULL
) ENGINE MergeTree() ORDER BY s_suppkey;

-- Partsupp table
CREATE OR REPLACE TABLE {{ schema }}.partsupp (
    ps_partkey INTEGER NOT NULL,
    ps_suppkey INTEGER NOT NULL,
    ps_availqty INTEGER NOT NULL,
    ps_supplycost DECIMAL(15,2) NOT NULL,
    ps_comment VARCHAR(199) NOT NULL
) ENGINE MergeTree() ORDER BY (ps_partkey, ps_suppkey);

-- Customer table
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

-- Orders table
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

-- Lineitem table
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
