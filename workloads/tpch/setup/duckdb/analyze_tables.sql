-- DuckDB TPC-H Statistics Analysis
-- DuckDB automatically collects statistics during data loading.
-- This file runs ANALYZE to ensure statistics are up-to-date.

ANALYZE {{ schema }}.nation;
ANALYZE {{ schema }}.region;
ANALYZE {{ schema }}.part;
ANALYZE {{ schema }}.supplier;
ANALYZE {{ schema }}.partsupp;
ANALYZE {{ schema }}.customer;
ANALYZE {{ schema }}.orders;
ANALYZE {{ schema }}.lineitem;
