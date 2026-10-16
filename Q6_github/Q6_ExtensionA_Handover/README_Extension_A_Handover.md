# Q6 to Extension A handover

All results are from the original Q6 notebook, using Q5 data. No forecasting model is included.

## Results
- `results/Q6_config.json`: TAA settings and asset ordering.
- `results/Q6_rolling_means.csv`: annualised 60-month rolling expected-return estimates by investment month.
- `results/Q6_rolling_covariances.csv`: annualised 9x9 rolling sample covariance, in long row-matrix form (9 rows per investment month).
- `results/Q6_taa_weights.csv`: monthly optimal TAA weights, expected return/volatility and growth exposure.
- `results/Q6_monthly_returns_wealth.csv`: date-aligned TAA and Q5 Balanced SAA realised monthly returns and cumulative wealth.
- `results/Q6_performance.csv`: benchmark performance metrics.

## Rolling-estimate dates and information cut-off
In `Q6_rolling_means.csv` and `Q6_rolling_covariances.csv`, `Date` identifies the **investment month** to which an estimate applies, not the final observation used to estimate it. `Estimation_start` and `Estimation_end` identify the first and last monthly return observations in the preceding **60-month estimation window**. For example, the estimate for `Date = 2016-01-29` uses returns from `2011-01-31` through `2015-12-31`, inclusive. The covariance file contains nine `Asset_Row` records for each investment month; together they form the 9x9 covariance matrix. `T0` is a reference field and should **not** be treated as a rolling information cut-off; use `Estimation_end` for that purpose.

Each rolling estimate is based only on the preceding 60 months of data available before the relevant investment month. Extension A must preserve the same information cut-off: all forecast features, model fitting, parameter tuning and portfolio decisions must use only information available at that decision time, without future returns or other look-ahead information.

## Source
- `data/`: original Q5 handover data; retain for rerunning the notebook.
- `Q6_full_analysis.ipynb`: original Q6 code and saved outputs.

## Extension A tasks and required outputs (not completed by Q6)
Choose and document the **forecasting method**, **forecast target** (e.g., expected returns, volatility or correlation), **forecast horizon**, input data and information cut-off. Explain how the forecasts are generated out of sample and evaluate their predictive performance with suitable out-of-sample metrics.

Retain the forecasts and their dates, forecast-based portfolio weights and realised monthly returns, portfolio performance metrics (including risk and final wealth), and a comparison against both the **Q6 historical-estimate TAA** and **Q5 Balanced-SAA** benchmarks on identical out-of-sample dates. Report the forecast evaluation results and the portfolio comparison in a form suitable for the final group report. Q5 Balanced SAA has annual strategic-weight updates and monthly rebalancing; it is not a single unchanging weight vector across the full period.

## Integrating forecasts with Q6 optimisation
Forecast-based TAA should retain Q6's mean-variance optimisation objective, the baseline risk-aversion parameter **gamma = 5**, the same nine assets and their ordering, monthly rebalancing, no short-selling, individual weight bounds **0%-50%**, and tactical deviations of **+/-10 percentage points** relative to the **corresponding year's Q5 Balanced-SAA weights**. Preserve the baseline zero-transaction-cost assumption for like-for-like comparisons.

Replace **only the estimated input(s) targeted by the forecasting model** (for example, expected returns, or the relevant volatility/covariance estimates) with forecasts available at the decision date; keep the remaining inputs and assumptions aligned with Q6 unless a deviation is explicitly documented and separately analysed. This helps isolate the contribution of the forecasting approach rather than confounding it with changes in constraints or optimisation settings. Avoid future information throughout.
