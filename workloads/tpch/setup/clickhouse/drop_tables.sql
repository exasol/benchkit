-- ClickHouse TPC-H Table Cleanup
-- Drops all TPC-H tables

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS {{ schema }}.lineitem;
DROP TABLE IF EXISTS {{ schema }}.orders;
DROP TABLE IF EXISTS {{ schema }}.customer;
DROP TABLE IF EXISTS {{ schema }}.partsupp;
DROP TABLE IF EXISTS {{ schema }}.supplier;
DROP TABLE IF EXISTS {{ schema }}.part;
DROP TABLE IF EXISTS {{ schema }}.region;
DROP TABLE IF EXISTS {{ schema }}.nation;

{% if node_count > 1 %}
-- Multinode: Also drop local tables
DROP TABLE IF EXISTS {{ schema }}.lineitem_local;
DROP TABLE IF EXISTS {{ schema }}.orders_local;
DROP TABLE IF EXISTS {{ schema }}.customer_local;
DROP TABLE IF EXISTS {{ schema }}.partsupp_local;
DROP TABLE IF EXISTS {{ schema }}.supplier_local;
DROP TABLE IF EXISTS {{ schema }}.part_local;
DROP TABLE IF EXISTS {{ schema }}.region_local;
DROP TABLE IF EXISTS {{ schema }}.nation_local;
{% endif %}
