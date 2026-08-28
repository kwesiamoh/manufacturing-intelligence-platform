# Stage 5B production-loss accounting

## Accounting baseline

The formal technical-loss bridge uses one baseline:

**Theoretical output during planned production time at nominal line rate**

`Theoretical Capacity Units = Planned Production Time × Nominal Rate`

This is intentionally different from the production plan.

The production plan is a scheduling target. Nominal-rate capacity is the technical baseline used by OEE. Mixing the two in one loss bridge would create non-reconciling loss categories.

## Exact technical-loss bridge

For each shift:

`Technical Capacity Gap = Theoretical Capacity Units - Good Quantity`

The gap is decomposed exactly into:

`Availability Loss + Performance Loss + Quality Loss`

### Availability loss

`Theoretical Capacity Units - Operating Capacity Units`

where:

`Operating Capacity Units = Operating Time × Nominal Rate`

Availability loss is split into:

- planned downtime loss
- unplanned downtime loss

These two categories are mutually exclusive and sum to total availability loss.

### Changeover

Changeover is reported as a subset of planned downtime.

It must not be added again to planned downtime when calculating total loss, otherwise the same lost time would be counted twice.

### Performance loss

`Operating Capacity Units - Actual Quantity`

This captures reduced-speed loss while the line is operating.

### Quality loss

`Actual Quantity - Good Quantity`

which equals rejected units in the Stage 3 production model.

## OEE identity

Because the same technical baseline is used:

`OEE = Good Quantity / Theoretical Capacity Units`

This should equal:

`Availability × Performance × Quality`

The Stage 5B validation checks this identity.

## Production-plan shortfall

A second metric is retained separately:

`Plan Shortfall Units = max(Planned Quantity - Good Quantity, 0)`

This measures delivery against the production plan.

It is not added to the OEE technical-loss bridge because the plan and technical capacity are different baselines.

## Financial translation

Each product has a synthetic internal standard unit opportunity value defined during Stage 3I.

The values are:

- Still Water: EUR 0.12/unit
- Sparkling Water: EUR 0.15/unit
- Cola Soft Drink: EUR 0.18/unit
- Citrus Soft Drink: EUR 0.18/unit
- Orange Juice Drink: EUR 0.28/unit
- Energy Drink: EUR 0.35/unit

These are **not** retail prices, observed margins, audited costs, or booked accounting losses.

They are portfolio-project assumptions used to translate lost production opportunity into a common EUR measure.

For this reason the SQL fields use the term `opportunity_eur`, not `revenue_loss` or `profit_loss`.

## Financial bridge

`Total Technical Opportunity EUR`

equals:

`Planned Downtime Opportunity EUR`
`+ Unplanned Downtime Opportunity EUR`
`+ Performance Opportunity EUR`
`+ Quality Opportunity EUR`

Changeover opportunity EUR remains a subset of planned-downtime opportunity EUR and is not added again.
