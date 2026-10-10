# Q2 handover for Q3-Q6

## Agreed baseline

- All weights sum to one.
- Each weight lies in [0,0.50]: no short selling and a 50% per-index cap.
- No minimum holding is required. An index can receive zero weight.
- The cap enforces the rule that no index receives more capital than all others combined. It controls capital concentration, not underlying-stock overlap or equal risk contributions.
- Uncapped long-only, 40%/30% caps and unrestricted signed portfolios are comparisons, not alternative baselines to mix into later questions.

Use `results/Q2_baseline_config.json` for the full-precision full-sample m, C, constraints and asset order. Match covariance rows/columns and weights to that order. Returns are decimal rates, so 0.08 means 8%; covariance is in squared decimal-return units.

## Q1 inputs retained

Monthly simple returns: 248 observations, 31 January 2006 to 31 August 2026. The 10-year and 5-year alternatives use the last 120 and 60 monthly returns. Annualised m = 12 times monthly mean; C = 12 times sample monthly covariance (ddof=1). Annualised volatility is the square root of annualised variance.

Q1 used a common sample without filling missing prices or deleting zero returns. Monthly frequency addresses inconsistent update frequency; it does not independently establish the absence of index smoothing. Currency comparability and price/total-return definitions remain qualifications requiring attention.

## Main full-sample results

GMV: expected return 3.9403%, volatility 1.3834%.

| Index | GMV weight |
| --- | ---: |
| BAUBIL | 50.0000% |
| H03432AU | 17.7956% |
| HEDGNAV | 16.7665% |
| BACM0 | 15.4379% |
| All remaining indices | 0% within numerical precision |

Efficient expected-return interval: 3.9403%-9.5866%. At a 3% minimum requirement, GMV is returned because it already exceeds the requirement. Requirements above the maximum are infeasible under these full-sample inputs and bounds.

| Minimum return requirement | Fitted annualised volatility |
| --- | ---: |
| 4% | 1.4132% |
| 6% | 4.5457% |
| 8% | 8.1858% |

These target requirements illustrate the frontier; **8% is not a fixed target for the remaining assignment**. Exact weights are in the baseline allocation CSVs.

The cap does not eliminate parameter sensitivity. At 8%, the 50% allocation changes from FDCIISAH under full-sample estimates to HEDGNAV under both recent windows. Results are fitted historical comparisons, not demonstrated future performance.

## What each later question still needs

### Q3: growth/defensive portfolios

Verify the APRA classification of every supplied index and any growth fraction before imposing 30/70, 70/30 and 90/10 growth/defensive requirements. The supplied APRA methodology is in `documents/APRA_MySuper_Methodology.pdf`. Q2 does not contain an approved nine-index growth mapping. Check feasibility jointly with the 50% limits; do not assume the growth targets are feasible. The optional Q2 CSV argument supplies a linear-program feasibility check once fractions are verified.

Apply the agreed baseline constraints plus the Q3 requirements. Calculate the requested GMV and Sharpe portfolios using a justified risk-free rate consistent with the return period and units. Q2 has not fixed a risk-free rate.

### Q4: utility and estimation uncertainty

Retain the chosen mandate and use the assignment's expected-utility problem, normal benchmark, Monte Carlo and historical bootstrap as requested. Justify risk-aversion values and numerical settings. Q2 has not set risk aversion, simulation counts or bootstrap settings. Keep monthly/annual units consistent with the modelled horizon.

### Q5: historical out-of-sample evaluation

At each decision date T0, estimate parameters using only returns available at T0, construct the requested Q3 strategies, and evaluate subsequent returns under the assignment's fixed-weight convention. Repeat the specified dates. The full-sample inputs ending in August 2026 must not be used to construct portfolios at earlier dates. Specify the meaning of fixed weights and any rebalancing convention consistently.

### Q6: tactical deviations

Build on a selected strategic allocation with justified tactical bounds. Re-estimate using only information available at each decision date. Evaluate the requested expected-utility, realised performance, turnover and sensitivity measures. Q2 has not set tactical bounds or a rebalancing rule. Check that strategic/tactical and individual-index constraints remain jointly feasible.

## Useful files

- `results/Q2_baseline_config.json`: primary full-sample inputs and constraints.
- `results/Q2_parameters_*.csv` and `Q2_covariance_*.csv`: all three estimation periods.
- `inputs/Q1_exports/Q1_clean_monthly_returns.csv`: histories for bootstrap and date-restricted estimation.
- `results/Q2_baseline_GMV_allocations.csv`: GMV results for all periods.
- `results/Q2_baseline_target_returns.csv`: selected capped-frontier allocations for all periods.
- `results/Q2_results.json`: full frontier weights, unrestricted benchmarks and validation.
- `report/Q2_Complete_Report.pdf`: final report incorporating the user's edits.

The JSON has null values for fixed_target, risk_free_rate and risk_aversion_gamma deliberately: these choices are not supplied by Q2. Q3 feasibility is explicitly marked not checked until a verified growth mapping is provided.
