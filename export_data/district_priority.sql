SELECT
    provinsi_name
    , kabupaten_name
    , kecamatan_name
    , COUNT(DISTINCT id) numVisit
FROM `merchant_success_analytics.retail_visit_ssot`
GROUP BY ALL
ORDER BY 4 DESC