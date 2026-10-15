# Q6 fixed-SAA input interface (Q6 is not solved)

This folder is self-contained for consuming Q5 benchmark inputs.
All ISO dates and asset orders are exact; weights/means/returns/volatility are decimals.
Q5_configuration.json specifies exact asset order, Growth fractions, targets, constraints,
windows, annualisation, solver settings and retrospective classification assumption.

| File | Contents / units |
|---|---|
| Q5_windows.csv | 10 T0 calendar cutoffs, actual estimation/OOS endpoints, 60/12 counts |
| Q5_weights.csv | 30 dated labelled weight vectors; nine asset columns in exact Q1 order |
| Q5_means.csv | 10 dated vectors m; annualised arithmetic decimal returns |
| Q5_covariances.csv | 90 rows: T0, Row_asset and nine ordered columns; C in annualised decimal return squared |
| Q5_asset_returns.csv | 120 dated OOS asset return vectors, with originating T0; monthly simple decimals |
| Q5_portfolio_returns.csv | 360 dated portfolio returns, T0/label, Block_wealth, Linked_wealth |
| Q5_performance.csv | 30 dated predicted/realised return-risk comparisons, compound returns, rankings |
| Q1_historical_monthly_returns_through_2025.csv | 240 historical asset-return rows, January 2006–December 2025; for historical input availability |

Q5 uses fixed-weight monthly rebalancing within each 12-month block, no intra-block
re-optimisation and zero transaction costs. For the corresponding Q6 fixed benchmark,
select the agreed SAA label and T0, retrieve its weights and compare on that block's exact
dates. Do not update the fixed benchmark with tactical decisions. Keep units, annualisation,
Growth definitions and exposure limits consistent. Select only information dated at or before
each Q6 decision cutoff from the historical file; later rows are not available at earlier cutoffs.
This folder does not specify tactical rebalancing dates, gamma, deviation bounds or forecasts.

Join weights/metrics on (T0, Portfolio); join means/covariance/windows/asset returns on T0.
Reconstruct C with Row_asset in configuration asset order. Do not assume alphabetical order.
Block_wealth resets to 1 at T0; Linked_wealth is the annually updated 2016–2025 sequence,
not a single fixed long-term SAA weight vector. Compare only matched horizons.
The summary/figures are presentation aids; use these unrounded CSV inputs for Q6.
Growth classifications have a retrospective full-sample rationale, an acknowledged potential
look-ahead limitation. Publication lags, currency and total-return definitions are unverified.
The source and validation records are in ../01_code and ../05_documentation.
