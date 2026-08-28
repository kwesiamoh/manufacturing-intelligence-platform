-- Stage 5B — Synthetic internal financial assumptions for production-loss valuation.
-- These are portfolio-project assumptions, not observed market prices or accounting ledger values.

CREATE TABLE IF NOT EXISTS cfg_product_loss_value (
    product_code VARCHAR(50) PRIMARY KEY,
    standard_loss_value_eur_per_unit NUMERIC(12,4) NOT NULL CHECK (standard_loss_value_eur_per_unit >= 0),
    value_basis VARCHAR(100) NOT NULL,
    assumption_class VARCHAR(50) NOT NULL,
    notes TEXT
);

INSERT INTO cfg_product_loss_value
    (product_code, standard_loss_value_eur_per_unit, value_basis, assumption_class, notes)
VALUES
    ('BEV-WAT-STILL',   0.1200, 'STANDARD_UNIT_OPPORTUNITY_VALUE', 'SYNTHETIC_INTERNAL', 'Synthetic internal portfolio assumption; not retail price or realized margin.'),
    ('BEV-WAT-SPARK',   0.1500, 'STANDARD_UNIT_OPPORTUNITY_VALUE', 'SYNTHETIC_INTERNAL', 'Synthetic internal portfolio assumption; not retail price or realized margin.'),
    ('BEV-CSD-COLA',    0.1800, 'STANDARD_UNIT_OPPORTUNITY_VALUE', 'SYNTHETIC_INTERNAL', 'Synthetic internal portfolio assumption; not retail price or realized margin.'),
    ('BEV-CSD-CITRUS',  0.1800, 'STANDARD_UNIT_OPPORTUNITY_VALUE', 'SYNTHETIC_INTERNAL', 'Synthetic internal portfolio assumption; not retail price or realized margin.'),
    ('BEV-JUI-ORANGE',  0.2800, 'STANDARD_UNIT_OPPORTUNITY_VALUE', 'SYNTHETIC_INTERNAL', 'Synthetic internal portfolio assumption; not retail price or realized margin.'),
    ('BEV-ENE-CLASSIC', 0.3500, 'STANDARD_UNIT_OPPORTUNITY_VALUE', 'SYNTHETIC_INTERNAL', 'Synthetic internal portfolio assumption; not retail price or realized margin.')
ON CONFLICT (product_code) DO UPDATE SET
    standard_loss_value_eur_per_unit = EXCLUDED.standard_loss_value_eur_per_unit,
    value_basis = EXCLUDED.value_basis,
    assumption_class = EXCLUDED.assumption_class,
    notes = EXCLUDED.notes;
