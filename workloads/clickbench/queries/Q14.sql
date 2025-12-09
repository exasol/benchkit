SELECT SearchEngineID, SearchPhrase, COUNT(*) AS c
FROM hits
{% if system_kind == 'exasol' %}
WHERE SearchPhrase IS NOT NULL
{% else %}
WHERE SearchPhrase <> ''
{% endif %}
GROUP BY SearchEngineID, SearchPhrase
ORDER BY c DESC LIMIT 10;

