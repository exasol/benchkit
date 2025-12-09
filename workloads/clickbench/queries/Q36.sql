SELECT URL, COUNT(*) AS PageViews
FROM hits
WHERE CounterID = 62 AND EventDate >= '2013-07-01' AND EventDate <= '2013-07-31' AND DontCountHits = 0 AND IsRefresh = 0
{% if system_kind == 'exasol' %}
AND URL IS NOT NULL
{% else %}
AND URL <> ''
{% endif %}
GROUP BY URL
ORDER BY PageViews DESC LIMIT 10;

