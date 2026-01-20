-- Trino TPC-H Table Creation
-- Creates external tables using Parquet files from storage backend
-- Data is read directly from Parquet files - zero copy loading

-- Nation table
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

-- Region table
CREATE TABLE IF NOT EXISTS {{ schema }}.region (
    r_regionkey INTEGER,
    r_name VARCHAR(25),
    r_comment VARCHAR(152)
)
WITH (
    format = 'PARQUET',
    external_location = '{{ data_locations.region }}'
);

-- Part table
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

-- Supplier table
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

-- Partsupp table
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

-- Customer table
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

-- Orders table
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

-- Lineitem table
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
