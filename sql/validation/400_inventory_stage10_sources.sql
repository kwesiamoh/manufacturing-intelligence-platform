\pset pager off
\echo '=== Stage 10A source-view inventory ==='

WITH target_views(view_name) AS (
    VALUES
        ('vw_shift_production_kpi'),
        ('vw_shift_production_loss'),
        ('vw_line_daily_kpi'),
        ('vw_site_daily_kpi'),
        ('vw_shift_loss_accounting'),
        ('vw_line_daily_loss_accounting'),
        ('vw_site_daily_loss_accounting'),
        ('vw_site_loss_summary'),
        ('vw_line_performance_summary'),
        ('vw_line_performance_rank'),
        ('vw_downtime_reason_pareto'),
        ('vw_changeover_summary'),
        ('vw_site_production_benchmark'),
        ('vw_site_production_rank'),
        ('vw_shift_energy_kpi'),
        ('vw_line_daily_energy_kpi'),
        ('vw_site_daily_energy_kpi'),
        ('vw_shift_energy_detail_kpi'),
        ('vw_site_auxiliary_energy_kpi'),
        ('vw_line_idle_energy_summary'),
        ('vw_compressed_air_line_summary'),
        ('vw_site_auxiliary_summary'),
        ('vw_site_auxiliary_rank'),
        ('vw_site_shift_electricity_cost_benchmark'),
        ('vw_site_electricity_cost_summary'),
        ('vw_site_electricity_cost_rank'),
        ('vw_country_semester_electricity_price_benchmark'),
        ('vw_data_quality_latest'),
        ('vw_data_quality_summary'),
        ('vw_data_quality_enterprise_summary')
)
SELECT
    tv.view_name,
    CASE WHEN v.table_name IS NOT NULL THEN 'FOUND' ELSE 'MISSING' END AS status
FROM target_views tv
LEFT JOIN information_schema.views v
    ON v.table_schema = 'public'
   AND v.table_name = tv.view_name
ORDER BY tv.view_name;

\echo ''
\echo '=== Column inventory for Stage 10 source views ==='

WITH target_views(view_name) AS (
    VALUES
        ('vw_shift_production_kpi'),
        ('vw_shift_production_loss'),
        ('vw_line_daily_kpi'),
        ('vw_site_daily_kpi'),
        ('vw_shift_loss_accounting'),
        ('vw_line_daily_loss_accounting'),
        ('vw_site_daily_loss_accounting'),
        ('vw_site_loss_summary'),
        ('vw_line_performance_summary'),
        ('vw_line_performance_rank'),
        ('vw_downtime_reason_pareto'),
        ('vw_changeover_summary'),
        ('vw_site_production_benchmark'),
        ('vw_site_production_rank'),
        ('vw_shift_energy_kpi'),
        ('vw_line_daily_energy_kpi'),
        ('vw_site_daily_energy_kpi'),
        ('vw_shift_energy_detail_kpi'),
        ('vw_site_auxiliary_energy_kpi'),
        ('vw_line_idle_energy_summary'),
        ('vw_compressed_air_line_summary'),
        ('vw_site_auxiliary_summary'),
        ('vw_site_auxiliary_rank'),
        ('vw_site_shift_electricity_cost_benchmark'),
        ('vw_site_electricity_cost_summary'),
        ('vw_site_electricity_cost_rank'),
        ('vw_country_semester_electricity_price_benchmark'),
        ('vw_data_quality_latest'),
        ('vw_data_quality_summary'),
        ('vw_data_quality_enterprise_summary')
)
SELECT
    c.table_name AS view_name,
    c.ordinal_position,
    c.column_name,
    c.data_type
FROM information_schema.columns c
JOIN target_views tv
  ON tv.view_name = c.table_name
WHERE c.table_schema = 'public'
ORDER BY c.table_name, c.ordinal_position;

\echo ''
\echo '=== Row counts for available Stage 10 source views ==='

DO $$
DECLARE
    r record;
    cnt bigint;
BEGIN
    FOR r IN
        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = 'public'
          AND table_name IN (
              'vw_shift_production_kpi',
              'vw_shift_production_loss',
              'vw_line_daily_kpi',
              'vw_site_daily_kpi',
              'vw_shift_loss_accounting',
              'vw_line_daily_loss_accounting',
              'vw_site_daily_loss_accounting',
              'vw_site_loss_summary',
              'vw_line_performance_summary',
              'vw_line_performance_rank',
              'vw_downtime_reason_pareto',
              'vw_changeover_summary',
              'vw_site_production_benchmark',
              'vw_site_production_rank',
              'vw_shift_energy_kpi',
              'vw_line_daily_energy_kpi',
              'vw_site_daily_energy_kpi',
              'vw_shift_energy_detail_kpi',
              'vw_site_auxiliary_energy_kpi',
              'vw_line_idle_energy_summary',
              'vw_compressed_air_line_summary',
              'vw_site_auxiliary_summary',
              'vw_site_auxiliary_rank',
              'vw_site_shift_electricity_cost_benchmark',
              'vw_site_electricity_cost_summary',
              'vw_site_electricity_cost_rank',
              'vw_country_semester_electricity_price_benchmark',
              'vw_data_quality_latest',
              'vw_data_quality_summary',
              'vw_data_quality_enterprise_summary'
          )
        ORDER BY table_name
    LOOP
        EXECUTE format('SELECT count(*) FROM public.%I', r.table_name) INTO cnt;
        RAISE NOTICE '% = % rows', r.table_name, cnt;
    END LOOP;
END $$;
