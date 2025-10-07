-- TPC-H Table Analysis Script
-- Analyzes tables and updates statistics for optimal query performance

{% if system_kind == 'exasol' %}
-- Analyze database to estimate statistics for query optimization
ANALYZE DATABASE ESTIMATE STATISTICS;
COMMIT;
{% elif system_kind == 'clickhouse' %}
-- ClickHouse automatically maintains statistics
-- OPTIMIZE can be run to merge data parts and improve performance
OPTIMIZE TABLE {{ schema }}.nation FINAL;
OPTIMIZE TABLE {{ schema }}.region FINAL;
OPTIMIZE TABLE {{ schema }}.part FINAL;
OPTIMIZE TABLE {{ schema }}.supplier FINAL;
OPTIMIZE TABLE {{ schema }}.partsupp FINAL;
OPTIMIZE TABLE {{ schema }}.customer FINAL;
OPTIMIZE TABLE {{ schema }}.orders FINAL;
OPTIMIZE TABLE {{ schema }}.lineitem FINAL;

SELECT 'Table optimization completed for ClickHouse';
{% else %}
{{ UNSUPPORTED_SYSTEM_KIND_ERROR_FOR[system_kind] }}
{% endif %}
