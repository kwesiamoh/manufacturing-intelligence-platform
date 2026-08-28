# Value Realization Framework

## 1. Establish baseline

For every use case, record:

- baseline period;
- metric definition;
- source system;
- business owner;
- current performance;
- known seasonality / operating context.

## 2. Define intervention

Examples:

- maintenance action;
- line-setting change;
- energy operating-policy change;
- quality corrective action;
- planning adjustment.

Analytics alone should not be credited with benefit. The intervention enabled
by the analytics must be identifiable.

## 3. Measure post-intervention performance

Compare against:

- approved historical baseline;
- matched operating conditions where possible;
- control/reference lines or periods when available.

## 4. Convert to financial value

Use finance-approved unit economics:

- contribution margin per good unit;
- electricity cost;
- labor cost;
- maintenance cost;
- scrap/rework cost.

Do not use portfolio assumptions as real-company finance inputs.

## 5. Record confidence

Suggested confidence categories:

- Confirmed: finance-approved realized benefit
- Validated: operational improvement observed, financial conversion pending
- Estimated: model-based opportunity
- Exploratory: analytical indication only

The current synthetic technical-opportunity values belong to **Estimated /
model-based opportunity**, not Confirmed.

## 6. Benefit ledger

A production implementation should maintain a benefit ledger with:

- use-case ID;
- site/line;
- owner;
- baseline;
- action;
- observed improvement;
- gross benefit;
- overlap adjustment;
- net benefit;
- confidence status;
- approval date.

This prevents multiple dashboards or domains from claiming the same financial
benefit.
