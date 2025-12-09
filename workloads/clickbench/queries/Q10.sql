SELECT MobilePhoneModel, COUNT(DISTINCT UserID) AS u
FROM hits
{% if system_kind == 'exasol' %}
WHERE MobilePhoneModel IS NOT NULL
{% else %}
WHERE MobilePhoneModel <> ''
{% endif %}
GROUP BY MobilePhoneModel
ORDER BY u DESC LIMIT 10;

