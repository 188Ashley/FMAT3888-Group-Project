# Q4 results and units

All weights/returns/volatilities are decimal fractions. Covariance is in squared decimal-return units. Gamma is measured for wealth normalised to W0=1. The one-period model represents one year; the annual inputs are arithmetic estimates, not CAGR.

The authoritative asset order is stored in Q4_config_and_validation.json. Every covariance row/column and weight array uses that order. The fitted reference is the full-sample normal model, not a future realised distribution.

| Output | Meaning |
| --- | --- |
| Q4a_benchmark.csv | Optimal fitted allocations, annualised mean/volatility, CE return/wealth, normal expected utility and benchmark timing |
| Q4a_gamma_design_sweep.csv | Preliminary preference scenarios from 0.01 to 250 supporting the selected range |
| Q4b_MC_runs.csv | Every MC method/sample-size/replicate/gamma allocation, exact-model mean/risk, CE regret, estimation error and timing |
| Q4b_MC_summary.csv | Scenario-level aggregation of the eight MC replications |
| Q4b_*_rep0_samples.npz | Representative full simulated asset-return vectors for replication zero at each method/sample size |
| Q4c_bootstrap_distributions.npz | IID arrays: weights (B, gamma, asset), means (B, asset), covariances (B, asset, asset), row indices (B, monthly observation), gamma labels and asset labels |
| Q4c_bootstrap_runs.csv | Every IID resampled optimum, its distance from fitted weights and its model-evaluated CE regret |
| Q4c_allocation_uncertainty.csv | Marginal mean/SD/2.5%-97.5% weight ranges; zero/cap frequencies using tolerance 1e-7 |
| Q4c_stability_summary.csv | Allocation distance and model-evaluated CE regret by gamma |
| Q4c_replication_convergence.csv | First B/2 versus all B: largest changes in mean weights and percentile endpoints |
| Q4c_block_L*_distributions.npz | Joint moving-block weights and sampled block starts; reconstruct row indices using starts + offsets, concatenate and truncate to 248 rows |
| Q4c_block_bootstrap_runs.csv | Individual moving-block allocations and allocation distances |
| Q4c_block_allocation_uncertainty.csv | Moving-block marginal weight summaries |
| Q4c_block_stability_summary.csv | Moving-block distances and cash-weight summaries by length and gamma |
| Q4_config_and_validation.json | Inputs, model/horizon, seed tree, settings, source hashes, lag-one diagnostics, limiting portfolios and optimisation validation |
| Q4_independent_checks.json | Independent utility/gradient/export/bootstrap reconstruction checks |

CE return = x.T m - gamma/2 x.T C x. CE regret is the fitted benchmark CE return minus the MC/resampled portfolio CE return, evaluated under the ORIGINAL fitted m/C. It is an internal model diagnostic, not realised out-of-sample underperformance. Multiply by 10,000 to express CE return differences in basis points.

Half-L1 distance = 0.5*sum(abs(x - x_reference)). It is the fraction of capital allocated differently, not historical turnover.

For MC, N counts total return vectors. Antithetic MC therefore uses N/2 independent pairs; pair members are not independent. The numerical solver minimises the stable log of the sampled exponential expectation, not a sample mean-variance proxy.

Timing excludes data loading/writing. `solver_seconds` measures optimisation with draws already available. `shared_generation_seconds` measures generation of the complete vector sample reused across gammas; `amortised_total_seconds` adds an equal share of this one-time cost to the solver time. BLAS is limited to one thread. Reference timing is the median of 30 quadratic solves per gamma.

Percentile ranges are marginal resampling distributions, not joint feasible allocations or guaranteed 95% confidence coverage. Block results use fewer resamples and are approximate dependence checks. All representative simulated samples are retained; remaining samples can be regenerated from the saved seed tree and experiment order in the code.
