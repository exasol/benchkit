-- TPC-H Table Cleanup Script
-- Drops all TPC-H tables and schema

{% if system_kind == 'exasol' %}
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
{% elif system_kind == 'clickhouse' %}
-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS {{ schema }}.lineitem;
DROP TABLE IF EXISTS {{ schema }}.orders;
DROP TABLE IF EXISTS {{ schema }}.customer;
DROP TABLE IF EXISTS {{ schema }}.partsupp;
DROP TABLE IF EXISTS {{ schema }}.supplier;
DROP TABLE IF EXISTS {{ schema }}.part;
DROP TABLE IF EXISTS {{ schema }}.region;
DROP TABLE IF EXISTS {{ schema }}.nation;
{% else %}
{{ UNSUPPORTED_SYSTEM_KIND_ERROR_FOR[system_kind] }}
{% endif %}
