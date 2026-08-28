# Data-quality and interpretation notes

Statistics Canada attaches data-quality symbols to estimates. These must be retained because the table's
published notes define quality categories using coefficient-of-variation ranges.

This dataset is aggregate survey data at manufacturing-industry level. It is therefore suitable for
benchmarking and calibration, not direct machine/line telemetry.

The category `Water for cooling, condensing and steam` is especially useful for the project's utility
layer, but it is a combined purpose category. It must not be split into separate cooling-water and steam
volumes without another source.

A later Gold benchmark can safely calculate:
- water intake by industry and year;
- share used as process water;
- share used for cooling/condensing/steam;
- changes between survey years;
- industry comparison.

It cannot safely calculate:
- water per production line;
- water per SKU;
- hourly water demand;
- site-specific European utility cost.
