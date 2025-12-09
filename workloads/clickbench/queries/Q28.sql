SELECT REGEXP_REPLACE(Referer, '^https?://(?:www\.)?([^/]+)/.*$', '\1') AS k, AVG(length(Referer)) AS l, COUNT(*) AS c, MIN(Referer)
FROM hits 
{% if system_kind == 'exasol' %}
WHERE Referer IS NOT NULL
{% else %}
WHERE Referer <> ''
{% endif %}
GROUP BY REGEXP_REPLACE(Referer, '^https?://(?:www\.)?([^/]+)/.*$', '\1')
HAVING COUNT(*) > 100000 
ORDER BY l DESC LIMIT 25;

