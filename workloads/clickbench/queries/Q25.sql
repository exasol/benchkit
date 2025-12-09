SELECT SearchPhrase FROM hits
{% if system_kind == 'exasol' %}
WHERE SearchPhrase IS NOT NULL
{% else %}
WHERE SearchPhrase <> ''
{% endif %}
ORDER BY SearchPhrase LIMIT 10;

