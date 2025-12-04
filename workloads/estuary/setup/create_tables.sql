-- Estuary Table Creation Script
-- Creates the TPC-H tables used for the estuary warehouse benchmark

{% if system_kind == 'exasol' %}
-- Exasol table creation

CREATE OR REPLACE TABLE {{ schema }}.region (
    r_regionkey DEC(11),
    r_name CHAR(25) CHARACTER SET ASCII,
    r_comment VARCHAR(152) CHARACTER SET ASCII
);

INSERT INTO "REGION" ("R_REGIONKEY", "R_NAME", "R_COMMENT") VALUES
(1, 'AMERICA                  ', 'hs use ironic, even requests. s'),
(0, 'AFRICA                   ', 'lar deposits. blithely final packages cajole. regular waters are final requests. regular accounts are according to '),
(2, 'ASIA                     ', 'ges. thinly even pinto beans ca'),
(3, 'EUROPE                   ', 'ly final courts cajole furiously final excuse'),
(4, 'MIDDLE EAST              ', 'uickly special accounts cajole carefully blithely close requests. carefully final asymptotes haggle furiousl');
;

CREATE OR REPLACE TABLE {{ schema }}.nation (
    n_nationkey DEC(11),
    n_name CHAR(25) CHARACTER SET ASCII,
    n_regionkey DEC(11),
    n_comment VARCHAR(152) CHARACTER SET ASCII
);

INSERT INTO "NATION" ("N_NATIONKEY", "N_NAME", "N_REGIONKEY", "N_COMMENT") VALUES
(20, 'SAUDI ARABIA             ', 4, 'ts. silent requests haggle. closely express packages sleep across the blithely'),
(21, 'VIETNAM                  ', 2, 'hely enticingly express accounts. even, final '),
(22, 'RUSSIA                   ', 3, ' requests against the platelets use never according to the quickly regular pint'),
(23, 'UNITED KINGDOM           ', 3, 'eans boost carefully special requests. accounts are. carefull'),
(13, 'JORDAN                   ', 4, 'ic deposits are blithely about the carefully regular pa'),
(24, 'UNITED STATES            ', 1, 'y final packages. slow foxes cajole quickly. quickly silent platelets breach ironic accounts. unusual pinto be'),
(0, 'ALGERIA                  ', 0, ' haggle. carefully final deposits detect slyly agai'),
(17, 'PERU                     ', 1, 'platelets. blithely pending dependencies use fluffily across the even pinto beans. carefully silent accoun'),
(18, 'CHINA                    ', 2, 'c dependencies. furiously express notornis sleep slyly regular accounts. ideas sleep. depos'),
(1, 'ARGENTINA                ', 1, 'al foxes promise slyly according to the regular accounts. bold requests alon'),
(2, 'BRAZIL                   ', 1, 'y alongside of the pending deposits. carefully special packages are about the ironic forges. slyly special '),
(19, 'ROMANIA                  ', 3, 'ular asymptotes are about the furious multipliers. express dependencies nag above the ironically ironic account'),
(6, 'FRANCE                   ', 3, 'refully final requests. regular, ironi'),
(3, 'CANADA                   ', 1, 'eas hang ironic, silent packages. slyly regular packages are furiously over the tithes. fluffily bold'),
(4, 'EGYPT                    ', 4, 'y above the carefully unusual theodolites. final dugouts are quickly across the furiously regular d'),
(11, 'IRAQ                     ', 4, 'nic deposits boost atop the quickly final requests? quickly regula'),
(12, 'JAPAN                    ', 2, 'ously. final, express gifts cajole a'),
(5, 'ETHIOPIA                 ', 0, 'ven packages wake quickly. regu'),
(14, 'KENYA                    ', 0, ' pending excuses haggle furiously deposits. pending, express pinto beans wake fluffily past t'),
(15, 'MOROCCO                  ', 0, 'rns. blithely bold courts among the closely regular packages use furiously bold platelets?'),
(16, 'MOZAMBIQUE               ', 0, 's. ironic, unusual asymptotes wake blithely r'),
(7, 'GERMANY                  ', 3, 'l platelets. regular accounts x-ray: unusual, regular acco'),
(8, 'INDIA                    ', 2, 'ss excuses cajole slyly across the packages. deposits print aroun'),
(9, 'INDONESIA                ', 2, ' slyly express asymptotes. regular deposits haggle slyly. carefully ironic hockey players sleep blithely. carefull'),
(10, 'IRAN                     ', 4, 'efully alongside of the slyly final dependencies. ');


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

CREATE OR REPLACE TABLE {{ schema }}.partsupp (
    ps_partkey DEC(8),
    ps_suppkey DEC(8),
    ps_availqty DEC(10),
    ps_supplycost DECIMAL(12,2),
    ps_comment VARCHAR(256),
    DISTRIBUTE BY ps_partkey
);

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


create or replace lua scalar script string_split(input_string varchar(256), delimiter char(1)) emits (word varchar(256))
as
function run(ctx)
    if ctx.input_string ~= null then
        for s in string.gmatch(ctx.input_string, "([^"..ctx.delimiter.." ]+)") do
            ctx.emit(s)
        end
    end
end
;

create or replace lua scalar script quersumme(input_string varchar(256)) returns integer
as
function run(ctx)
    sum = 0
    if ctx.input_string ~= null then
        for s in string.gmatch(ctx.input_string, '%d') do
            -- lua auto-converts strings to integer
            sum = sum + s
        end
    end
    return decimal(sum, 18, 0)
end
;

{% else %}
{{ UNSUPPORTED_SYSTEM_KIND_ERROR_FOR[system_kind] }}
{% endif %}

commit;
