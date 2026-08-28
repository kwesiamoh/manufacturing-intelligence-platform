# Stage 6B energy-detail fields

| Field | Meaning |
|---|---|
| line_production_electricity_kwh | Stage 3H line electricity attributed to production load |
| line_idle_electricity_kwh | Stage 3H line electricity attributed to idle load |
| line_total_electricity_kwh | Production + idle line electricity |
| idle_energy_share | Idle electricity / total line electricity |
| compressed_air_nm3 | Modeled synthetic compressed-air volume; can-line rows use the existing quantity formula and remain distinct from real external basis information |
| compressed_air_nm3_per_1000_units | Synthetic line-class design intensity per thousand actual units; `CAN_ENERGY_250 = 5.0 Nm³/1,000 cans`, while PET values remain unchanged |
| site_auxiliary_base_kw | Synthetic site auxiliary base electrical load |
| site_weather_auxiliary_kw | Synthetic weather-sensitive auxiliary electrical load |
| mean_air_temperature_c | Real ERA5-Land external weather context |
| site_auxiliary_electricity_kwh | Auxiliary electricity over the shift |
| site_total_electricity_kwh | Line electricity + auxiliary electricity |
| auxiliary_energy_share | Auxiliary electricity / site total electricity |
