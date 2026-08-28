# Stage 3G — Maintenance Work Orders

## Purpose
Create a coherent fictional maintenance history linked directly to the Stage 3E beverage-line downtime events.

## Source-of-truth relationship
Maintenance is not generated independently.

A corrective maintenance work order can only be created from an existing unplanned downtime event when:
- the failure category is mechanical or electrical; and
- the stop duration is long enough to plausibly require a maintenance intervention.

Every generated work order retains:
- `downtime_event_id`
- `production_record_id`
- `site_code`
- `line_code`
- `equipment_code`
- `shift_code`
- `product_code`

This provides a traceable relationship:

production shift -> downtime event -> maintenance work order

The current generator creates at most one work order for each qualifying
downtime row and validates the current output as one-to-one. The canonical fact
model does not make that a universal constraint: future maintenance sources may
record multiple work orders for one downtime event, while each work order still
has only one downtime reference.

## Cost fields
Monetary maintenance cost fields are intentionally left null in Stage 3G.

The project will define a small, documented financial-parameter set later and then calculate labor/material/other costs consistently. This avoids inventing arbitrary monetary values now.

## Scope boundary
This stage creates corrective maintenance only.

It does not create a full preventive-maintenance scheduling system, spare-parts inventory, technician roster, CMMS workflow, maintenance approvals, or purchasing process.

The real FMUCD dataset remains an external maintenance benchmark/reference source and is not relabelled as beverage-plant maintenance.

## Validation
The generator verifies that:
- every maintenance work order has a valid downtime-event parent;
- start/end times are valid;
- the maintenance interval lies within the linked downtime interval.
