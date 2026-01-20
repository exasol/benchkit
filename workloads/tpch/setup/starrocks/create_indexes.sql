-- StarRocks TPC-H Index Creation
-- StarRocks uses DUPLICATE KEY ordering and Bloom filters automatically
-- The DUPLICATE KEY clause in table definitions provides primary sort order
-- Additional optimization comes from DISTRIBUTED BY hash partitioning
-- No explicit index creation needed - optimization via table definition

SELECT 'StarRocks: Using table sort keys and hash distribution for optimization';
