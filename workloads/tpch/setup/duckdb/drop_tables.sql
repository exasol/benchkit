-- DuckDB TPC-H Table Drop
-- Drops all 8 TPC-H tables

DROP TABLE IF EXISTS {{ schema }}.lineitem;
DROP TABLE IF EXISTS {{ schema }}.orders;
DROP TABLE IF EXISTS {{ schema }}.partsupp;
DROP TABLE IF EXISTS {{ schema }}.customer;
DROP TABLE IF EXISTS {{ schema }}.supplier;
DROP TABLE IF EXISTS {{ schema }}.part;
DROP TABLE IF EXISTS {{ schema }}.nation;
DROP TABLE IF EXISTS {{ schema }}.region;
