SELECT SearchPhrase, MIN(URL), MIN(Title), COUNT(*) AS c, COUNT(DISTINCT UserID)
FROM hits
WHERE Title LIKE '%Google%' AND URL NOT LIKE '%.google.%'
{% if system_kind == 'exasol' %}
AND SearchPhrase IS NOT NULL
{% else %}
AND SearchPhrase <> ''
{% endif %}
GROUP BY SearchPhrase
ORDER BY c DESC LIMIT 10;

