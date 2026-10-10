# Data dictionary

## Asset order

1. ASA52 Index
2. NDDLWI Index
3. NDLEEGF Index
4. RDAU Index
5. FDCIISAH Index
6. HEDGNAV Index
7. BACM0 Index
8. H03432AU Index
9. BAUBIL Index

Use exact labels to align data. Never infer alignment from alphabetical order.

## Units and estimates

- Weight: fraction of portfolio capital (0.50 = 50%).
- Return, volatility and target: decimal rates (0.08 = 8%). Report percentages multiply by 100.
- Variance/covariance: squared decimal-return units.
- Annualised mean: monthly simple-return mean multiplied by 12.
- Annualised covariance: monthly sample covariance multiplied by 12, ddof=1.
- Annualised portfolio volatility: sqrt(w.T @ C @ w).
- Mean annualisation is arithmetic, not CAGR or an exact compounded-return distribution.

## Input files

`inputs/Q1_exports/Q1_clean_monthly_returns.csv` has a Date column and nine asset columns. All observations are monthly simple returns, not prices. `Q1_baseline_parameters.csv` contains the original Q1 full-sample asset estimates. `Q1_results.xlsx` includes the Q1 audit and alternative estimation-window matrices; the original code's header offsets are intentional.

`inputs/raw/Bloomber_data.xlsx` is the original Bloomberg export with Daily, Weekly and Monthly sheets. It has not been modified. Its SHA256 is 0441477d277505722f0f39bc0c0a572889f55024123c3c8d9ff4c4e1e9edaa28.

## Output files

| File | Content |
| --- | --- |
| Q2_baseline_config.json | Full-sample m/C, exact asset order, adopted constraints, frontier interval and intentionally unset later-question parameters |
| Q2_parameters_full_sample.csv | Annualised asset means and volatilities for 248 returns |
| Q2_parameters_recent_10_years.csv | Annualised asset means and volatilities for 120 returns |
| Q2_parameters_recent_5_years.csv | Annualised asset means and volatilities for 60 returns |
| Q2_covariance_*.csv | Annualised labelled 9-by-9 covariance matrices for the corresponding periods |
| Q2_baseline_GMV_allocations.csv | Adopted capped GMV means, volatility and weights for all periods |
| Q2_baseline_target_returns.csv | Adopted capped portfolios at selected requirements for all periods |
| Q2_baseline_allocation_sensitivity.csv | Half-L1 allocation distances from full-sample weights |
| Q2_portfolios.csv | GMV, 81-point frontier, selected requirements and below-GMV validation portfolios for all long-only cases |
| Q2_cap_comparison.csv | Matched-requirement comparisons against uncapped long-only, including volatility cost |
| Q2_parameter_sensitivity.csv | Cross-window portfolio comparisons |
| Q2_results.json | All inputs, full frontier allocations, selected portfolios, signed benchmarks and verification results |

The `target` field is a minimum requirement; `expected_return` or `achieved_return` is the portfolio's achieved mean. Below GMV's mean these are different. The long-only case names are `Baseline: 50% cap`, `Uncapped benchmark`, `Comparison: 40% cap` and `Comparison: 30% cap`.

Half-L1 distance is 0.5 * sum(abs(w_alt - w_full)); it measures capital allocated differently, not realised trading turnover. Model/window means and volatilities are evaluated using that window's own estimated parameters.

Signed portfolios are unconstrained mathematical comparisons without gross-exposure bounds or financing/borrow costs. They are not the adopted investable baseline.

`FILE_SHA256.json` covers every committed package file except itself. The checksum manifest is a snapshot and should be regenerated if packaged files change.
