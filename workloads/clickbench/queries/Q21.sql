SELECT SearchPhrase, MIN(URL), COUNT(*) AS c
FROM hits 
WHERE URL LIKE '%google%'
{% if system_kind == 'exasol' %}
AND SearchPhrase IS NOT NULL
{% else %}
AND SearchPhrase <> ''
{% endif %}
GROUP BY SearchPhrase
ORDER BY c DESC LIMIT 10;

