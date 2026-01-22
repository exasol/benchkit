-- Trino TPC-H Table Analysis
-- Analyze tables to collect statistics for query optimization
-- ANALYZE collects column statistics that help the optimizer choose better join orders
-- and estimate cardinalities for cost-based optimization

ANALYZE {{ schema }}.nation;
ANALYZE {{ schema }}.region;
ANALYZE {{ schema }}.part;
ANALYZE {{ schema }}.supplier;
ANALYZE {{ schema }}.partsupp;
ANALYZE {{ schema }}.customer;
ANALYZE {{ schema }}.orders;
ANALYZE {{ schema }}.lineitem;

SELECT 'Trino: Table statistics collected for query optimization';
