# Integration policy

1. Never present unrelated public datasets as if they came from one physical company.
2. Preserve the original source, industry, geography and licensing/provenance metadata.
3. Use real measured rows unchanged in Bronze.
4. Apply cleaning/normalization only in Silver with documented lineage.
5. Benchmark/survey data may calibrate assumptions but cannot be row-level joined to operational data without a genuine key.
6. Any future synthetic enterprise record must carry provenance fields showing that it is synthetic and which real source(s) informed its distribution or rule.
7. Gold KPIs must distinguish measured, derived, benchmark-derived and synthetic-calibrated values.
