# Q4 handover

Q4(a)-(c) is complete. It uses Q1's current full-sample monthly data and Q2's full investment/no-short/50% cap. The checkpoint explicitly excludes the three Q3 growth targets from Q4.

## Five preference scenarios

| gamma | Annual expected return | Annual volatility |
| --- | ---: | ---: |
| 1 | 9.551% | 11.623% |
| 5 | 8.510% | 9.252% |
| 10 | 6.611% | 5.609% |
| 25 | 4.732% | 2.441% |
| 100 | 3.982% | 1.398% |

These are illustrative scenarios spanning allocation regimes, not an estimate of a uniquely appropriate risk-aversion value. Use exact weights in results/Q4a_benchmark.csv rather than rounded report values.

## Q4(b)

The exact normal utility problem reduces to maximising m.T x - gamma/2 x.T C x. Direct numerical expected-utility optimisation agrees increasingly closely as simulated N rises. Standard and antithetic MC were compared over three sample sizes and eight independent repetitions. Antithetic sampling improves aggregate accuracy in this experiment. Use the quadratic benchmark for this model; MC is slower and approximate.

## Q4(c)

10,000 IID joint-month bootstrap resamples show substantial allocation uncertainty. At gamma=10, median half-L1 distance from the fitted weights is 48.30%, and several marginal allocation ranges extend from zero to the 50% cap. Moving joint blocks of 6/12/24 months preserve some observed serial dependence; the 12-month median distance at gamma=10 is 48.71%. This is not actual trading turnover or realised future performance.

Some tail endpoints remain noisy because constrained weights have point masses at zero/cap. The report documents replication sensitivity instead of claiming all percentiles have converged.

## Downstream interfaces

- Q5 is independent of Q4 and retains the three Q3 growth-target strategies. Do not replace its SAA weights with a Q4 gamma portfolio automatically.
- Q6 needs a separately justified gamma and tactical limits. Q4 gives preference-sensitivity evidence, not a mandated value.
- Extension A may reuse the normal model/configuration, representative simulated returns, full historical returns and bootstrap distributions. It must still investigate distributions/forecasting and out-of-sample performance itself.
- Annual m/C model corresponds to one-year normal ARITHMETIC return, not compounded wealth over twelve months. Maintain compatible time scales in any later utility calculation.

## Retained outputs

Configuration includes full-precision m/C, asset order, horizon, constraints, gammas, seeds and validation. Compressed NPZ files retain IID bootstrap weights, reestimated means/covariances and sampled row indices, moving-block weights/starts, and representative MC asset-return vectors. Every simulated/resampled portfolio's weights are available in CSV. Original monthly returns are bundled in inputs/.

See report/Q4_Complete_Report.pdf and README.md. The report includes a Q4(a)-(c)/checkpoint coverage table. Original Q1/Q2/Q3 files were not altered.
