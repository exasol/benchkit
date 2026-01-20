-- Exasol TPC-H Table Cleanup
-- Drops all TPC-H tables

SET AUTOCOMMIT OFF;

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS {{ schema }}.lineitem;
DROP TABLE IF EXISTS {{ schema }}.orders;
DROP TABLE IF EXISTS {{ schema }}.customer;
DROP TABLE IF EXISTS {{ schema }}.partsupp;
DROP TABLE IF EXISTS {{ schema }}.supplier;
DROP TABLE IF EXISTS {{ schema }}.part;
DROP TABLE IF EXISTS {{ schema }}.region;
DROP TABLE IF EXISTS {{ schema }}.nation;

COMMIT;
