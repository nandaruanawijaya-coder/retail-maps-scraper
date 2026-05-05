WITH
    distinct_kelurahan AS (
        SELECT DISTINCT
            kecamatan_name,
            kabupaten_name,
            provinsi_name,
            kd_provinsi,
            kd_kabupaten,
            kd_kecamatan
        FROM
            `ledger-fcc1e.trb_pymnts_derived.geojson_indo_lookup`
    ),
    aggregation AS (
        SELECT DISTINCT
            CONCAT (lu.kd_provinsi, lu.kd_kabupaten, lu.kd_kecamatan) AS district_id,
            lu.kecamatan_name,
            lu.kabupaten_name,
            lu.provinsi_name
        FROM
            distinct_kelurahan lu
    )
SELECT
    *
FROM
    aggregation