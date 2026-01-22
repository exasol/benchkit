-- StarRocks TPC-H Table Creation
-- Uses OLAP engine with DUPLICATE KEY model for analytical queries
-- Supports multinode via replication_num property

CREATE TABLE IF NOT EXISTS {{ schema }}.nation (
    n_nationkey INT NOT NULL,
    n_name VARCHAR(25) NOT NULL,
    n_regionkey INT NOT NULL,
    n_comment VARCHAR(152)
)
ENGINE=OLAP
DUPLICATE KEY(n_nationkey)
DISTRIBUTED BY HASH(n_nationkey) BUCKETS {{ bucket_count | default(1) }}
PROPERTIES ("replication_num" = "{{ replication_num | default(1) }}");

CREATE TABLE IF NOT EXISTS {{ schema }}.region (
    r_regionkey INT NOT NULL,
    r_name VARCHAR(25) NOT NULL,
    r_comment VARCHAR(152)
)
ENGINE=OLAP
DUPLICATE KEY(r_regionkey)
DISTRIBUTED BY HASH(r_regionkey) BUCKETS {{ bucket_count | default(1) }}
PROPERTIES ("replication_num" = "{{ replication_num | default(1) }}");

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
DISTRIBUTED BY HASH(p_partkey) BUCKETS {{ bucket_count | default(8) }}
PROPERTIES ("replication_num" = "{{ replication_num | default(1) }}");

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
DISTRIBUTED BY HASH(s_suppkey) BUCKETS {{ bucket_count | default(4) }}
PROPERTIES ("replication_num" = "{{ replication_num | default(1) }}");

CREATE TABLE IF NOT EXISTS {{ schema }}.partsupp (
    ps_partkey INT NOT NULL,
    ps_suppkey INT NOT NULL,
    ps_availqty INT NOT NULL,
    ps_supplycost DECIMAL(15,2) NOT NULL,
    ps_comment VARCHAR(199) NOT NULL
)
ENGINE=OLAP
DUPLICATE KEY(ps_partkey, ps_suppkey)
DISTRIBUTED BY HASH(ps_partkey) BUCKETS {{ bucket_count | default(8) }}
PROPERTIES ("replication_num" = "{{ replication_num | default(1) }}");

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
DISTRIBUTED BY HASH(c_custkey) BUCKETS {{ bucket_count | default(8) }}
PROPERTIES ("replication_num" = "{{ replication_num | default(1) }}");

CREATE TABLE IF NOT EXISTS {{ schema }}.orders (
    o_orderkey BIGINT NOT NULL,
    o_custkey INT NOT NULL,
    o_orderstatus VARCHAR(1) NOT NULL,
    o_totalprice DECIMAL(15,2) NOT NULL,
    o_orderdate DATE NOT NULL,
    o_orderpriority VARCHAR(15) NOT NULL,
    o_clerk VARCHAR(15) NOT NULL,
    o_shippriority INT NOT NULL,
    o_comment VARCHAR(79) NOT NULL
)
ENGINE=OLAP
DUPLICATE KEY(o_orderkey)
DISTRIBUTED BY HASH(o_orderkey) BUCKETS {{ bucket_count | default(16) }}
PROPERTIES ("replication_num" = "{{ replication_num | default(1) }}");

CREATE TABLE IF NOT EXISTS {{ schema }}.lineitem (
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
    l_shipdate DATE NOT NULL,
    l_commitdate DATE NOT NULL,
    l_receiptdate DATE NOT NULL,
    l_shipinstruct VARCHAR(25) NOT NULL,
    l_shipmode VARCHAR(10) NOT NULL,
    l_comment VARCHAR(44) NOT NULL
)
ENGINE=OLAP
DUPLICATE KEY(l_orderkey)
DISTRIBUTED BY HASH(l_orderkey) BUCKETS {{ bucket_count | default(32) }}
PROPERTIES ("replication_num" = "{{ replication_num | default(1) }}");
