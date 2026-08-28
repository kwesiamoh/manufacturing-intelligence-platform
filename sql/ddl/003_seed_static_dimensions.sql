-- Manufacturing Intelligence Platform
-- Stage 2D: Seed static dimensions

INSERT INTO dim_utility (utility_code, utility_name, default_unit, utility_category)
VALUES
    ('ELECTRICITY', 'Electricity', 'kWh', 'ENERGY'),
    ('NATURAL_GAS', 'Natural Gas', 'kWh', 'ENERGY'),
    ('STEAM', 'Steam', NULL, 'THERMAL_UTILITY'),
    ('COMPRESSED_AIR', 'Compressed Air', NULL, 'UTILITY'),
    ('PROCESS_WATER', 'Process Water', 'm3', 'WATER'),
    ('COOLING_WATER', 'Cooling Water', 'm3', 'WATER'),
    ('CHILLED_WATER', 'Chilled Water', 'm3', 'WATER')
ON CONFLICT (utility_code) DO NOTHING;
