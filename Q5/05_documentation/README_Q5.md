# FMAT3888 Q5(a)–(c)

Executable: `01_code/Q5_full_analysis.py` (Python with NumPy, pandas, SciPy, Matplotlib).
From any directory: `python PATH/01_code/Q5_full_analysis.py`.
Defaults are resolved from the script location, not the current working directory.
Optional `--input-dir` and `--output-dir` select read-only inputs and a separate output folder.
Input: `C:\Users\kevin\Desktop\2026s2\fmat3888\group_project\Q5\codex_input`. No Q1–Q3 scripts execute or change.

## Files
- 02_results: windows (10); weights (30); means (10); covariance rows (90);
  asset returns (120); portfolio returns (360); performance (30, including ranks);
  stability (27 consecutive-date comparisons); validation (30 solver certificates);
  summary (3 portfolio rows with prediction errors, rankings and stability).
- 03_figures_tables: compact predicted/realised summary CSV; wealth and stability PNG/PDF figures.
- 04_Q6_HANDOFF: self-contained benchmark inputs, configuration and README.
- 05_documentation: this guide; methodology/assumptions; report-ready findings;
  validation JSON; SHA256/size output manifest (excludes itself).

All rate, volatility, exposure and weight fields are decimal fractions. Multiply by 100
for percentages. Covariance is annualised decimal return squared. Dates are ISO format.
The summary is the mean across ten annual tests; mean within-block volatility differs
from pooled 120-month volatility. Mean arithmetic annual return is not CAGR.
`OOS_compounded_return` is each 12-month block's compound return.
`Block_wealth` resets to 1 at every T0; `Linked_wealth` compounds all 120 OOS months,
with new target weights at each December boundary. It is an annually updated sequence
of SAA benchmarks, not a single unchanged ten-year weight vector.

## Validation and reproducibility
Every optimisation must pass explicit tolerances; failure stops execution.
The convex linearisation gap bounds annual variance suboptimality by 1e-8 absolute
and 1e-6 relative (one part per million). The largest observed absolute gap is recorded.
Constraint residuals must be at most 1e-8; dual stationarity and complementarity at most 1e-8.
Q3's positive objective scaling is retained. Weights are not clipped or renormalised.
Input SHA256 hashes and software versions are recorded in Q5_validation_summary.json.
No random simulation is used. Same code, data and software yield deterministic outputs;
solver results across software versions may differ slightly within tolerances.
