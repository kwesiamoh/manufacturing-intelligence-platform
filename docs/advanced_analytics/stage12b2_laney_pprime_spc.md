# Stage 12B.2 — Laney p′ Reject-Proportion SPC

## Why the ordinary p-chart was revised

The initial p-chart was mathematically correct but diagnostically unsuitable for
the synthetic enterprise dataset.

The baseline itself produced more than 80% observations outside conventional
3-sigma binomial limits. With very large shift subgroup sizes, the theoretical
binomial standard error becomes extremely small. Extra process variation then
causes ordinary p-chart z-scores to become unrealistically large.

That condition is called **overdispersion**.

## Laney p′ method

The Laney p′ chart retains the p-chart center line but adjusts the expected
variation using a `sigma_z` factor derived from the moving ranges of standardized
baseline proportions.

For each baseline subgroup:

    z_i = (p_i - p_bar) / sqrt[p_bar(1-p_bar)/n_i]

The moving range of successive z-values is calculated, and:

    sigma_z = MR_bar / 1.128

The adjusted limits are then:

    UCL_i = p_bar + 3 * sigma_z * sqrt[p_bar(1-p_bar)/n_i]
    LCL_i = p_bar - 3 * sigma_z * sqrt[p_bar(1-p_bar)/n_i]

with limits clipped to [0,1].

A `sigma_z` greater than 1 indicates overdispersion relative to the simple
binomial model.

## Design

- subgroup: production shift
- segmentation: site + line + product
- baseline: 2024
- monitoring: 2025
- source: `SYNTHETIC_ENTERPRISE`
- real measured plant data: no

## Interpretation

`ABOVE_UCL` means the shift reject proportion is unusually high relative to the
historical baseline after correcting for extra-binomial variation.

`BELOW_LCL` is statistically unusual but may represent unusually good quality,
not a deterioration.

`IN_CONTROL` means the observation falls within the adjusted Laney limits.

These are statistical control limits, not engineering/customer specification
limits.

## Portfolio limitation

The source is the fictional enterprise integration layer. The output demonstrates
a defensible SPC workflow and should not be described as real beverage-plant
process evidence.

The original conventional p-chart view is retained only as a diagnostic showing
why the Laney adjustment was required.
