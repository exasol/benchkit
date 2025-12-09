SELECT SearchEngineID, ClientIP, COUNT(*) AS c, SUM(IsRefresh), AVG(ResolutionWidth) 
FROM hits 
{% if system_kind == 'exasol' %}
WHERE SearchPhrase IS NOT NULL
{% else %}
WHERE SearchPhrase <> ''
{% endif %}
GROUP BY SearchEngineID, ClientIP 
ORDER BY c DESC LIMIT 10;

