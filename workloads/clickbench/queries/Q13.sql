SELECT SearchPhrase, COUNT(DISTINCT UserID) AS u
FROM hits
{% if system_kind == 'exasol' %}
WHERE SearchPhrase IS NOT NULL
{% else %}
WHERE SearchPhrase <> ''
{% endif %}
GROUP BY SearchPhrase
ORDER BY u DESC LIMIT 10;

