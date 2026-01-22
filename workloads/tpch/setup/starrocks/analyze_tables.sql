-- StarRocks TPC-H Table Analysis
-- Collect table statistics for cost-based optimizer
-- StarRocks uses ANALYZE TABLE to collect statistics

ANALYZE TABLE {{ schema }}.nation;
ANALYZE TABLE {{ schema }}.region;
ANALYZE TABLE {{ schema }}.part;
ANALYZE TABLE {{ schema }}.supplier;
ANALYZE TABLE {{ schema }}.partsupp;
ANALYZE TABLE {{ schema }}.customer;
ANALYZE TABLE {{ schema }}.orders;
ANALYZE TABLE {{ schema }}.lineitem;

SELECT 'StarRocks: Statistics collected for query optimization';
