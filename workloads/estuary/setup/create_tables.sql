-- Estuary Table Creation Script
-- Creates the TPC-H tables used for the estuary warehouse benchmark

{% if system_kind == 'exasol' %}
-- Exasol table creation
{% elif system_kind == 'clickhouse' %}
-- ClickHouse table creation
{% else %}
{{ UNSUPPORTED_SYSTEM_KIND_ERROR_FOR[system_kind] }}
{% endif %}

-- Part table
{% if system_kind == 'exasol' %}
CREATE OR REPLACE TABLE {{ schema }}.part (
    p_partkey DEC(8),
    p_name VARCHAR(35) CHARACTER SET ASCII,
    p_mfgr CHAR(25) CHARACTER SET ASCII,
    p_brand CHAR(10) CHARACTER SET ASCII,
    p_type VARCHAR(10) CHARACTER SET ASCII,
    p_size DEC(1),
    p_container CHAR(10) CHARACTER SET ASCII,
    p_retailprice DECIMAL(12,2),
    p_comment VARCHAR(256),
    DISTRIBUTE BY p_partkey
);
{% elif system_kind == 'clickhouse' %}
CREATE OR REPLACE TABLE {{ schema }}.part (
    p_partkey INTEGER NOT NULL,
    p_name VARCHAR(256) NOT NULL,
    p_mfgr CHAR(25) NOT NULL,
    p_brand CHAR(10) NOT NULL,
    p_type VARCHAR(10) NOT NULL,
    p_size INTEGER NOT NULL,
    p_container CHAR(10) NOT NULL,
    p_retailprice DECIMAL(15,2) NOT NULL,
    p_comment VARCHAR(256) NOT NULL
) ENGINE MergeTree() ORDER BY p_partkey;
{% endif %}

-- Supplier table
{% if system_kind == 'exasol' %}
CREATE OR REPLACE TABLE {{ schema }}.supplier (
    s_suppkey DEC(8),
    s_name CHAR(256) CHARACTER SET ASCII,
    s_address VARCHAR(40) CHARACTER SET ASCII,
    s_nationkey DEC(2),
    s_phone CHAR(35) CHARACTER SET ASCII,
    s_acctbal DECIMAL(12,2),
    s_comment VARCHAR(256),
    DISTRIBUTE BY s_suppkey
);
{% elif system_kind == 'clickhouse' %}
CREATE OR REPLACE TABLE {{ schema }}.supplier (
    s_suppkey INTEGER NOT NULL,
    s_name CHAR(35) NOT NULL,
    s_address VARCHAR(40) NOT NULL,
    s_nationkey INTEGER NOT NULL,
    s_phone CHAR(35) NOT NULL,
    s_acctbal DECIMAL(15,2) NOT NULL,
    s_comment VARCHAR(256) NOT NULL
) ENGINE MergeTree() ORDER BY s_suppkey;
{% endif %}

-- Partsupp table
{% if system_kind == 'exasol' %}
CREATE OR REPLACE TABLE {{ schema }}.partsupp (
    ps_partkey DEC(8),
    ps_suppkey DEC(8),
    ps_availqty DEC(10),
    ps_supplycost DECIMAL(12,2),
    ps_comment VARCHAR(256),
    DISTRIBUTE BY ps_partkey
);
{% elif system_kind == 'clickhouse' %}
CREATE OR REPLACE TABLE {{ schema }}.partsupp (
    ps_partkey INTEGER NOT NULL,
    ps_suppkey INTEGER NOT NULL,
    ps_availqty INTEGER NOT NULL,
    ps_supplycost DECIMAL(15,2) NOT NULL,
    ps_comment VARCHAR(256) NOT NULL
) ENGINE MergeTree() ORDER BY (ps_partkey, ps_suppkey);
{% endif %}

-- Customer table
{% if system_kind == 'exasol' %}
CREATE OR REPLACE TABLE {{ schema }}.customer (
    c_custkey DEC(8),
    c_name VARCHAR(256) CHARACTER SET ASCII,
    c_address VARCHAR(40) CHARACTER SET ASCII,
    c_nationkey DEC(2),
    c_phone CHAR(35) CHARACTER SET ASCII,
    c_acctbal DECIMAL(12,2),
    c_mktsegment CHAR(10) CHARACTER SET ASCII,
    c_comment VARCHAR(256),
    DISTRIBUTE BY c_custkey
);
{% elif system_kind == 'clickhouse' %}
CREATE OR REPLACE TABLE {{ schema }}.customer (
    c_custkey INTEGER NOT NULL,
    c_name VARCHAR(256) NOT NULL,
    c_address VARCHAR(40) NOT NULL,
    c_nationkey INTEGER NOT NULL,
    c_phone CHAR(35) NOT NULL,
    c_acctbal DECIMAL(15,2) NOT NULL,
    c_mktsegment CHAR(10) NOT NULL,
    c_comment VARCHAR(256) NOT NULL
) ENGINE MergeTree() ORDER BY (c_mktsegment, c_custkey);
{% endif %}

-- Orders table
{% if system_kind == 'exasol' %}
CREATE OR REPLACE TABLE {{ schema }}.orders (
    o_orderkey DEC(8),
    o_custkey DEC(8),
    o_orderstatus CHAR(1) CHARACTER SET ASCII,
    o_totalprice DECIMAL(12,2),
    o_orderdate DATE,
    o_orderpriority CHAR(15) CHARACTER SET ASCII,
    o_clerk CHAR(35) CHARACTER SET ASCII,
    o_shippriority DEC(10),
    o_comment VARCHAR(256),
    DISTRIBUTE BY o_custkey
);
{% elif system_kind == 'clickhouse' %}
CREATE OR REPLACE TABLE {{ schema }}.orders (
    o_orderkey INTEGER NOT NULL,
    o_custkey INTEGER NOT NULL,
    o_orderstatus CHAR(1) NOT NULL,
    o_totalprice DECIMAL(12,2) NOT NULL,
    o_orderdate DATE NOT NULL,
    o_orderpriority CHAR(15) NOT NULL,
    o_clerk CHAR(35) NOT NULL,
    o_shippriority INTEGER NOT NULL,
    o_comment VARCHAR(256) NOT NULL,
    DISTRIBUTE BY o_orderkey,
    PARTITION BY o_orderdate
) ENGINE MergeTree() ORDER BY (o_orderdate, o_orderkey);
{% endif %}

-- Lineitem table
{% if system_kind == 'exasol' %}
CREATE OR REPLACE TABLE {{ schema }}.lineitem (
    l_orderkey DEC(8),
    l_partkey DEC(8),
    l_suppkey DEC(8),
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
    l_comment VARCHAR(256),
    DISTRIBUTE BY l_orderkey
);
{% elif system_kind == 'clickhouse' %}
CREATE OR REPLACE TABLE {{ schema }}.lineitem (
    l_orderkey INTEGER NOT NULL,
    l_partkey INTEGER NOT NULL,
    l_suppkey INTEGER NOT NULL,
    l_linenumber INTEGER NOT NULL,
    l_quantity DECIMAL(12,2) NOT NULL,
    l_extendedprice DECIMAL(12,2) NOT NULL,
    l_discount DECIMAL(12,2) NOT NULL,
    l_tax DECIMAL(12,2) NOT NULL,
    l_returnflag CHAR(1) NOT NULL,
    l_linestatus CHAR(1) NOT NULL,
    l_shipdate DATE NOT NULL,
    l_commitdate DATE NOT NULL,
    l_receiptdate DATE NOT NULL,
    l_shipinstruct CHAR(25) NOT NULL,
    l_shipmode CHAR(10) NOT NULL,
    l_comment VARCHAR(256) NOT NULL
) ENGINE MergeTree() ORDER BY (l_shipdate, l_orderkey, l_partkey);
{% endif %}

commit;
