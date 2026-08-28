# Stage 13E.1 — Condition Monitoring Feasibility

This stage determines whether the real Step 04 hydraulic condition-monitoring
dataset supports a defensible condition classification or degradation analysis.

It does not train a model.

The script checks:

- non-telemetry Silver files;
- cycle-level metadata/labels;
- low-cardinality condition fields;
- cycle coverage;
- sensor coverage;
- whether telemetry cycles and condition labels can be aligned.

## Decision rule

Proceed to Stage 13E modeling only if:

1. cycle-level condition labels exist;
2. label-to-cycle alignment is complete or nearly complete;
3. the target classes have useful representation;
4. the resulting task is genuinely condition monitoring rather than a
   fabricated predictive-maintenance claim.

## Provenance

Step 04 `HYDRAULIC_CM` is a real external condition-monitoring source and must
remain separate from the synthetic beverage-enterprise maintenance layer.

## Run

```powershell
python -m pip install -r .\scripts\requirements_stage13e1.txt
python .\scripts\profile_stage13e1_condition_monitoring.py
```
