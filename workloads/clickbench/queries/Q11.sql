SELECT MobilePhone, MobilePhoneModel, COUNT(DISTINCT UserID) AS u FROM hits
{% if system_kind == 'exasol' %}
WHERE MobilePhoneModel IS NOT NULL
{% else %}
WHERE MobilePhoneModel <> ''
{% endif %}
GROUP BY MobilePhone, MobilePhoneModel
ORDER BY u DESC LIMIT 10;

