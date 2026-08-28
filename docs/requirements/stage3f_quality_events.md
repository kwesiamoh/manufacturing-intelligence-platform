# Stage 3F — Beverage Quality Events

## Purpose
Generate beverage-relevant quality events from the Stage 3D production records.

## Core rule
`reject_quantity` in the Stage 3D production layer remains the source of truth.

For every production record:
- the sum of `rejected_units` in detailed quality events must equal `reject_quantity`;
- the generator stops if any production record fails this reconciliation.

## Defect taxonomy
Only beverage-relevant defects are used:
- fill-volume defects
- cap/closure defects
- carbonation deviations
- label/print defects
- bottle visual/deformation defects
- product/process-quality deviations for juice
- can seam defects
- can damage
- coding defects

## Scope boundary
This stage does not attempt laboratory chemistry, microbiology, HACCP, food-safety certification, SPC control-limit modelling, or regulatory compliance.

Those would expand the project beyond the defined manufacturing-intelligence scope.

## Data classification
All events are:
- `SYNTHETIC_OPERATIONAL`
- `SYNTHETIC_INTEGRATION`

The SECOM dataset remains a real semiconductor quality/process reference source and is not relabelled as beverage data.
