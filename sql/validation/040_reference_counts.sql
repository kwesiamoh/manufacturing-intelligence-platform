SELECT 'ref_itac_assessment' AS table_name, COUNT(*) AS row_count FROM ref_itac_assessment
UNION ALL SELECT 'ref_itac_recommendation', COUNT(*) FROM ref_itac_recommendation
UNION ALL SELECT 'ref_fmucd_maintenance', COUNT(*) FROM ref_fmucd_maintenance
UNION ALL SELECT 'ref_statcan_water', COUNT(*) FROM ref_statcan_water
UNION ALL SELECT 'ref_eia_mecs', COUNT(*) FROM ref_eia_mecs
UNION ALL SELECT 'ref_eu_ets', COUNT(*) FROM ref_eu_ets
UNION ALL SELECT 'ref_eurostat_energy_price', COUNT(*) FROM ref_eurostat_energy_price
ORDER BY table_name;

\echo '=== Mandatory reference-count gate ==='
DO $validation$
DECLARE
    expected record;
    actual_count bigint;
BEGIN
    FOR expected IN
        SELECT * FROM (VALUES
            ('ref_itac_assessment', 22901::bigint, true),
            ('ref_itac_recommendation', 169953::bigint, true),
            ('ref_fmucd_maintenance', 3731442::bigint, true),
            ('ref_statcan_water', 676::bigint, true),
            ('ref_eia_mecs', 3368::bigint, true),
            ('ref_eu_ets', 84056::bigint, true),
            ('ref_eurostat_energy_price', 1::bigint, false)
        ) AS x(table_name, expected_count, exact_match)
    LOOP
        EXECUTE format('SELECT COUNT(*) FROM %I', expected.table_name)
        INTO actual_count;
        IF (expected.exact_match AND actual_count <> expected.expected_count)
           OR (NOT expected.exact_match AND actual_count < expected.expected_count) THEN
            RAISE EXCEPTION 'Reference % has % rows; expected % %',
                expected.table_name,
                actual_count,
                CASE WHEN expected.exact_match THEN 'exactly' ELSE 'at least' END,
                expected.expected_count;
        END IF;
    END LOOP;
END
$validation$;
