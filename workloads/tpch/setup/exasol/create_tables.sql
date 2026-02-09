-- Exasol TPC-H Table Creation
-- Creates all 8 TPC-H tables with Exasol-specific data types and distribution

-- Drop tables in reverse FK dependency order for clean re-runs
-- (keeps schema intact so the active connection remains valid)
DROP TABLE IF EXISTS {{ schema }}.lineitem;
DROP TABLE IF EXISTS {{ schema }}.orders;
DROP TABLE IF EXISTS {{ schema }}.partsupp;
DROP TABLE IF EXISTS {{ schema }}.customer;
DROP TABLE IF EXISTS {{ schema }}.supplier;
DROP TABLE IF EXISTS {{ schema }}.part;
DROP TABLE IF EXISTS {{ schema }}.nation;
DROP TABLE IF EXISTS {{ schema }}.region;

-- Nation table
CREATE OR REPLACE TABLE {{ schema }}.nation (
    n_nationkey DEC(11),
    n_name CHAR(25) CHARACTER SET ASCII,
    n_regionkey DEC(11),
    n_comment VARCHAR(152) CHARACTER SET ASCII
);

-- Region table
CREATE OR REPLACE TABLE {{ schema }}.region (
    r_regionkey DEC(11),
    r_name CHAR(25) CHARACTER SET ASCII,
    r_comment VARCHAR(152) CHARACTER SET ASCII
);

-- Part table
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

-- Supplier table
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

-- Partsupp table
CREATE OR REPLACE TABLE {{ schema }}.partsupp (
    ps_partkey DEC(11),
    ps_suppkey DEC(11),
    ps_availqty DEC(10),
    ps_supplycost DECIMAL(12,2),
    ps_comment VARCHAR(199) CHARACTER SET ASCII,
    DISTRIBUTE BY ps_partkey
);

-- Customer table
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

-- Orders table
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

-- Lineitem table
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
