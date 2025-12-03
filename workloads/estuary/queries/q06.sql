-- Query 6
-- Description: Analyzes combined comments from orders and line items to find the top 5 most frequent words each month, excluding common stop words, using string manipulation and tokenization via LATERAL VIEW EXPLODE.
-- Difficulty: Hard
WITH combined_comments AS (
    SELECT
        TO_CHAR(O.O_ORDERDATE, 'yyyy - MMMM') AS order_month,
        LOWER(TRIM(REGEXP_REPLACE(O.O_COMMENT, '[^a-zA-Z0-9 ]', ''))) AS cleaned_comment
    FROM orders O

    UNION ALL

    SELECT
        TO_CHAR(O.O_ORDERDATE, 'yyyy - MMMM') AS order_month,
        LOWER(TRIM(REGEXP_REPLACE(L.L_COMMENT, '[^a-zA-Z0-9 ]', ''))) AS cleaned_comment
    FROM lineitem L
    JOIN orders O
        ON L.L_ORDERKEY = O.O_ORDERKEY
),
tokenized_words AS (
    SELECT
        order_month,
        cleaned_comment,
        trim(regexp_substr(cleaned_comment, '[^ ]+( |$)', 0, word_nr)) as word
    FROM combined_comments
    join ( values between 1 and 50 as T(word_nr) )
    on word_nr <= (LENGTH(cleaned_comment) - LENGTH(REPLACE(cleaned_comment, ' ', '')) + 1)
),
word_counts AS (
    SELECT
        order_month,
        word,
        COUNT(*) AS word_count,
        RANK() OVER (PARTITION BY order_month ORDER BY COUNT(*) DESC) AS rank
    FROM tokenized_words
    WHERE word NOT IN ('the', 'is', 'and', 'or', 'a', 'an', 'of', 'to', 'in', 'for', 'on', 'with', 'at')
    GROUP BY order_month, word
)
SELECT order_month, word, word_count
FROM word_counts
WHERE rank <= 5
ORDER BY order_month, word_count DESC
LIMIT 1000;
