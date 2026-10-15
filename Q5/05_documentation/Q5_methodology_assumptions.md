# Methodology and assumptions

Q5(a): For December T0 in 2015–2024, select exactly 60 monthly return observations,
January of T0 year minus four through December of T0 year. Use m=12*sample mean
and C=12*sample covariance (ddof=1). Optimise min w'Cw subject to sum(w)=1,
0<=w_i<=0.5, g'w=G, with G=0.30/0.70/0.90 and g=[1,1,1,1,1,0.5,0,0,0].
Reuse Q3 minimum_variance: HiGHS feasible start and SLSQP with analytic gradients,
100-fold objective scaling, ftol=1e-12 and maxiter=10000. Validate global optimality
using a linearisation LP over the same feasible set, plus dual residuals.

Q5(b): Hold target weights fixed for the following 12 months via monthly rebalancing:
Rp,t=w_T0'Rt. No intra-block estimation/optimisation. Ignore all transaction costs.
Predicted annual return=w'm; annual volatility=sqrt(w'Cw).
Realised annualised return=12*mean(Rp); realised annualised volatility=sqrt(12)*std(Rp,ddof=1).
Wealth=product(1+Rp). Predictions are arithmetic risk/return estimates, not compound forecasts.
Return and volatility errors are realised minus predicted. No Sharpe/risk-free proxy is introduced.

Q5(c): Compare these measures across ten non-overlapping OOS calendar years (2016–2025).
Rank realised arithmetic return and compounded return highest first, volatility lowest first;
ties share rank via method=min. Stability=0.5*sum(abs(w_k-w_previous)), for nine transitions.
This measures changes in target weights, not actual trading turnover after asset drift.

Calendar December month-end is T0. Original CSV dates are retained: some are last-business-day
labels. Selection uses monthly periods; no date filling or silent normalisation. December's
return is available at the assumed T0 close; OOS starts the following January.

## Limitations and look-ahead boundary
- Rolling moments use only returns ending at or before T0. Full-sample JSON/workbook
  means, covariance and Q3 cash proxy are never used in historical estimation or evaluation.
- Q3 Growth classifications remain fixed by agreement. Five classifications were justified
  with full-sample statistics through August 2026. Their retrospective use is a potential
  classification look-ahead limitation; this is not a fully point-in-time classification test.
- Historical index observation labels do not establish publication availability at T0.
  In particular, HEDGNAV's monthly updates may involve reporting lags or revisions.
- Q1 does not establish currency comparability or price-versus-total-return treatment for
  every index. Results apply to the supplied simple index returns, not verified investable returns.
- Each realised volatility uses only 12 observations, hence has substantial sampling uncertainty.
  Ten evaluation years do not establish future superiority or statistical significance.
- Monthly rebalancing and index exposure are treated as frictionless and executable.
  No costs, taxes, instrument access or liquidity constraints are modelled.
- The 50% cap is inherited policy, not a data-estimated optimum. Correlated indices may
  still create concentration; low-return cash leads to moderately ill-conditioned covariances.
- Q1_baseline_parameters.csv is absent from codex_input but unnecessary for Q5.
  No upstream rerun is required.

Requirements checked against official Q5(a)–(c), Q1 annualisation, Q2 constraints,
Q3 Growth classifications/optimiser, and the agreed Q4/Q5 checkpoint D1 handoff.
