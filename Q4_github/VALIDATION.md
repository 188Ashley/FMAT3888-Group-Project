# Q4 validation

- Current Q1 returns, workbook moments and Q2 baseline reconciled at full precision.
- All 65,245 main quadratic/MC/IID/block portfolio solutions passed primal and convex optimality-gap checks.
- Maximum primal violation: 5.440314865268192e-12; maximum convex optimality gap: 6.087724857385063e-08, below 1e-7.
- Fitted return and risk were non-increasing over selected risk aversion values.
- MC fitted-model CE values never exceeded the exact benchmark.
- Independent normal utility identity relative error below 9e-16; sampled-utility transformation relative error below 5e-16.
- Sampled-objective analytic gradient agreed with central finite differences within 5.5e-11.
- Twenty stored bootstrap mean/covariance estimates reconstructed exactly from stored row indices and original returns.
- Saved CSV/NPZ portfolio constraints checked independently.
- Fresh archive-extraction smoke run completed 2,065 portfolio solutions. It reproduced benchmark numerical results exactly, representative MC return arrays exactly, and first-two-replication MC weights within 1e-12. Timing values were excluded from numerical comparisons.
- Final nine-page user-edited PDF compiled without overfull/underfull warnings, and all final pages were rendered and visually inspected.

The historical bootstrap does not prove predictive accuracy. Moving-block results are dependence sensitivity checks; percentile convergence is reported honestly, including unstable low-gamma endpoints.

The final edited report and figures match the delivered formal report. Numerical inputs, results and analysis code are unchanged from the validated Q4 run. All compressed arrays and archive entries were checked for integrity during final packaging.
