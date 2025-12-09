SELECT CounterID, AVG(length(URL)) AS l, COUNT(*) AS c 
FROM hits 
{% if system_kind == 'exasol' %}
WHERE URL IS NOT NULL
{% else %}
WHERE URL <> ''
{% endif %}
GROUP BY CounterID
HAVING COUNT(*) > 100000 
ORDER BY l DESC LIMIT 25;

