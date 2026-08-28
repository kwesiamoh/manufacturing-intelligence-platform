# Project Risk Register

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R01 | Public datasets do not belong to one enterprise | High | High | synthetic integration layer + explicit provenance |
| R02 | Synthetic analytics mistaken for real plant results | Medium | High | source labels in docs and outputs |
| R03 | Power BI numeric compatibility failures | Low | Medium | `gold_bi` typed wrapper views |
| R04 | Credentials exposed in repository | Low | High | prompts/env vars, `.gitignore`, secret scanning |
| R05 | Data-quality warnings interpreted as passes | Medium | Medium | PASS/WARN/FAIL kept distinct |
| R06 | Proxy reliability metrics overstated | Medium | High | explicit MTBF/availability proxy wording |
| R07 | Analytical model overfitting | Medium | Medium | strict holdouts, baselines, stop-tuning rules |
| R08 | Experimental condition classes distort chronological split | High | Medium | class-wise chronological benchmark split with limitation note |
| R09 | Scope creep delays portfolio completion | Medium | Medium | follow 16-stage plan; defer nonessential refinements |
| R10 | Unintended AWS spend | Low | High | no live AWS deployment; €0 hard constraint |
| R11 | Missing production-loss or maintenance-cost data | Medium | Medium | do not report unsupported measures |
| R12 | Final repo contains obsolete diagnostic artifacts | Medium | Medium | Stage 16 cleanup and accepted-result inventory |
