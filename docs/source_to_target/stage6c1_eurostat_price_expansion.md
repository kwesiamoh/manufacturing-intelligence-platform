# Stage 6C.1 — Eurostat electricity-price expansion

## Source

Eurostat dataset `nrg_pc_205`: electricity prices for non-household consumers, bi-annual data.

## Purpose

The original Step 14 Silver layer contains only metadata. Stage 6C.1 expands the official dataset into observation-level records required for energy-cost benchmarking.

## Geography

Only these countries are retained in the focused Silver output:

- DE
- NL
- PL
- CZ
- FR
- ES

These correspond to the countries of the six fictional enterprise sites.

This is a geography mapping only. Eurostat records remain real external benchmark observations and are not represented as plant invoices or measured site tariffs.

## Period

Focused output:
- 2024
- 2025

## Bronze

The raw official JSON-stat response is retained unchanged.

## Silver

Two observation files are created:

- full decoded `nrg_pc_205` observations
- six-country 2024-2025 subset

The decoder preserves all dimensions returned by Eurostat rather than assuming dimension names beyond `geo` and `time`.

## Next step

Stage 6C.2 will inspect the actual returned dimensions, select a defensible non-household consumption band and tax basis, and calculate benchmark electricity cost for the fictional enterprise.

No tariff is selected in Stage 6C.1.
