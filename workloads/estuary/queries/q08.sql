-- Query 8
-- Description: Identifies customers with comments containing a specific term ('final'), counts their total comments, and aggregates their top 5 longest comments using ARRAY_AGG.
-- Difficulty: Hard
WITH order_comments AS (
    SELECT
        C.C_CUSTKEY,
        C.C_NAME,
        LOWER(TRIM(REGEXP_REPLACE(O.O_COMMENT, '[^a-zA-Z0-9 ]', ''))) AS cleaned_comment,
        CASE
            WHEN LENGTH(O.O_COMMENT) > 100 THEN 'LONG_COMMENT'
            ELSE 'SHORT_COMMENT'
        END AS comment_type
    FROM orders O
    JOIN customer C ON O.O_CUSTKEY = C.C_CUSTKEY
),
lineitem_comments AS (
    SELECT
        C.C_CUSTKEY,
        C.C_NAME,
        LOWER(TRIM(REGEXP_REPLACE(L.L_COMMENT, '[^a-zA-Z0-9 ]', ''))) AS cleaned_comment,
        CASE
            WHEN LENGTH(L.L_COMMENT) > 100 THEN 'LONG_COMMENT'
            ELSE 'SHORT_COMMENT'
        END AS comment_type
    FROM lineitem L
    JOIN orders O ON L.L_ORDERKEY = O.O_ORDERKEY
    JOIN customer C ON O.O_CUSTKEY = C.C_CUSTKEY
),
combined_comments AS (
    SELECT * FROM order_comments
    UNION ALL
    SELECT * FROM lineitem_comments
),
comment_counts AS (
    SELECT
        C_CUSTKEY,
        COUNT(*) AS total_comments
    FROM combined_comments
    GROUP BY C_CUSTKEY
),
filtered_comments AS (
    SELECT
        CC.C_CUSTKEY,
        CC.C_NAME,
        CC.CLEANED_COMMENT,
        CC.COMMENT_TYPE,
        COALESCE(CCC.TOTAL_COMMENTS, 0) AS total_comments
    FROM combined_comments CC
    LEFT JOIN comment_counts CCC ON CC.C_CUSTKEY = CCC.C_CUSTKEY
    WHERE CC.CLEANED_COMMENT LIKE '%final%'
),
ranked_comments AS (
    SELECT
        C_CUSTKEY,
        C_NAME,
        CLEANED_COMMENT,
        COMMENT_TYPE,
        TOTAL_COMMENTS,
        ROW_NUMBER() OVER (PARTITION BY C_CUSTKEY ORDER BY LENGTH(CLEANED_COMMENT) DESC) AS comment_rank
    FROM filtered_comments
)
SELECT
    RC.C_CUSTKEY,
    RC.C_NAME,
    GROUP_CONCAT(CONCAT(RC.CLEANED_COMMENT, ' (', RC.COMMENT_TYPE, ')')) AS customer_comments,
    MAX(RC.TOTAL_COMMENTS) AS total_comments_per_customer
FROM ranked_comments RC
WHERE RC.COMMENT_RANK <= 5
GROUP BY RC.C_CUSTKEY, RC.C_NAME
ORDER BY total_comments_per_customer DESC
LIMIT 1000;
