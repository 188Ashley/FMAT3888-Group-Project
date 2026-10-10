# Question 2: Static Portfolio Optimisation

## Overview and inputs

We use the expected-return vector m and covariance matrix C from Q1 to construct portfolios, subject to full investment, no short selling and a 50% limit on each index. The uncapped long-only portfolio is used as a benchmark for comparison of different index caps; 40% and 30% caps and unrestricted signed weights are alternative comparisons.

The analysis answers all four parts of Q2: constraints and efficient-frontier plots; the global minimum-variance portfolio; portfolios for a range of return requirements; and sensitivity to alternative Q1 estimates.

Q1 provides 248 simple monthly returns from 31 January 2006 to 31 August 2026, calculated from 249 common monthly index levels. Each index uses the same dates. We retain Q1's annualisation: m equals 12 times the average monthly return, and C equals 12 times the sample monthly covariance matrix, using denominator N - 1. These are annualised arithmetic estimates, not compound annual growth rates.

| Index | Annualised expected return | Annualised volatility |
| --- | ---: | ---: |
| ASA52 | 8.183% | 13.800% |
| NDDLWI | 9.571% | 14.095% |
| NDLEEGF | 9.602% | 16.096% |
| RDAU | 4.744% | 19.963% |
| FDCIISAH | 9.516% | 11.458% |
| HEDGNAV | 5.457% | 5.282% |
| BACM0 | 4.035% | 3.737% |
| H03432AU | 4.261% | 3.472% |
| BAUBIL | 3.289% | 0.565% |

For sensitivity analysis, we use the following Q1 estimation periods:

| Estimation period | Returns | First return | Last return |
| --- | ---: | ---: | ---: |
| Full sample | 248 | 2006-01-31 | 2026-08-31 |
| Recent 10 years | 120 | 2016-09-30 | 2026-08-31 |
| Recent 5 years | 60 | 2021-09-30 | 2026-08-31 |

The exported means and covariance matrices agree with calculations from the clean returns to floating-point precision. All three covariance matrices are positive definite. Calculations use full precision; the report rounds percentages for presentation. The methods are drawn from the supplied toolbox: Markowitz mean-variance optimisation, minimum-variance portfolios, efficient frontiers and restricted/unrestricted optimisation.

\newpage

## Q2(a): Portfolio constraints and efficient frontier

### Full investment and no short selling

Our main constraints are:

$$
\sum_{i=1}^{9}w_i=1,\qquad 0\leq w_i\leq0.50.
$$

1. The weights sum to one, ensuring full investment of available capital. Together with non-negative weights, this keeps gross exposure at 100%.
2. Only non-negative weights are permitted in the main model, so short selling is excluded. Allowing signed weights would permit leverage despite weights summing to one: 120% long and 20% short exposure gives 140% gross exposure.
3. The weight of any individual index cannot exceed 0.50. This limits capital concentration in any individual asset: no single index receives more capital than all remaining exposures combined.

The supplied index data do not specify short-borrow fees, financing costs, collateral requirements or executable short instruments. We therefore exclude short selling from the strategic baseline. This is a modelling choice, not an assignment prohibition.

### Justification of the 50% index cap

The project concerns a diversified investment fund, and Q2(a) explicitly asks us to consider limits on individual-asset exposure. We adopt the policy that **no single index receives more capital than all remaining indices combined**. Full investment gives:

$$
w_i\leq\sum_{j\ne i}w_j=1-w_i
\quad\Longleftrightarrow\quad w_i\leq0.50.
$$

The 50% cap is the least restrictive uniform cap satisfying this policy. A higher limit permits a majority allocation; a lower limit imposes stronger concentration control and requires an additional objective. The policy is a judgement about the fund's mandate, not a threshold estimated from the data or specified by the assignment.

The uncapped full-sample GMV portfolio allocates approximately 98.28% to BAUBIL. At an 8% return requirement, the largest uncapped weights are 55.74%, 75.66% and 79.51% across the three periods. These findings show that concentration control changes relevant solutions. They do not prove that a cap improves future performance.

The cap limits capital allocation to an index. It does not guarantee diversification of underlying securities or risk: two correlated indices could each receive 50%. No positive minimum holding is imposed.

\newpage

### Finding and plotting the efficient frontier

For each annual expected-return requirement $\mu$, we solve:

$$
\min_w\;w^\top Cw
\quad\text{subject to}\quad
m^\top w\geq\mu,\quad\mathbf1^\top w=1,\quad0\leq w_i\leq0.50.
$$

Portfolio expected return is $m^\top w$ and volatility is $\sqrt{w^\top Cw}$. We first find GMV without a return requirement and then maximise expected return under the same weight bounds. The full-sample efficient branch runs from **3.9403% to 9.5866% expected return**. We solve 81 requirements across this interval and plot achieved expected return against volatility. The point count controls plotting resolution.

![Figure 1. Full-sample efficient frontier for the adopted long-only, 50%-capped model. The marked GMV endpoint has expected return 3.940% and volatility 1.383%.](../figures/Q2_baseline_frontier.pdf)

Requirements below the GMV mean produce the same GMV portfolio; requirements above the maximum are infeasible. The figure shows the efficient branch, not the dominated lower-return branch.

\newpage

### Comparison with alternative constraints

At the same 8% expected-return requirement, annualised volatility is:

| Estimation period | Uncapped | 50% cap | 40% cap | 30% cap |
| --- | ---: | ---: | ---: | ---: |
| Full sample | 8.161% | 8.186% | 8.316% | 8.555% |
| Recent 10 years | 6.538% | 6.638% | 6.707% | 6.882% |
| Recent 5 years | 5.402% | 6.014% | 6.266% | 6.566% |

Compared with the uncapped portfolio, the 50%, 40% and 30% caps produce higher fitted volatility, with the increase becoming larger as the cap becomes more restrictive. We accept the increase under the 50% cap in exchange for limiting capital concentration in individual indices. This spreads capital across at least two indices, although it does not ensure that risk is evenly distributed.

The 50% cap increases volatility relative to the uncapped benchmark by approximately **0.024, 0.100 and 0.612 percentage points**, respectively. Its cost is small in the full sample but larger over five years. Tighter caps reduce the feasible set further and cannot lower minimum variance at a common feasible requirement.

We accept this efficiency cost to enforce the stated concentration policy. We do not claim that 50% is economically optimal or that the capped portfolio must outperform the benchmark.

To examine short selling separately, we compare uncapped long-only and unrestricted signed-weight portfolios at an 8% requirement:

| Estimation period | Uncapped long-only volatility | Unrestricted volatility | Gross exposure |
| --- | ---: | ---: | ---: |
| Full sample | 8.161% | 6.265% | 275.71% |
| Recent 10 years | 6.538% | 4.466% | 350.12% |
| Recent 5 years | 5.402% | 2.331% | 310.62% |

The unrestricted portfolios have no gross-exposure limit and omit borrowing and financing costs. Their lower fitted volatility comes with large offsetting positions.

![Figure 2. Full-sample comparisons of index caps and short-selling assumptions. The uncapped long-only curve separates the effect of the cap from the effect of permitting signed weights.](../figures/Q2a_alternative_frontiers.pdf)

\newpage

## Q2(b): Global minimum-variance portfolio

### Optimisation and allocation

The GMV portfolio solves:

$$
\min_w\;w^\top Cw
\quad\text{subject to}\quad
\mathbf1^\top w=1,\quad0\leq w_i\leq0.50.
$$

There is no expected-return requirement. With positive-definite C and linear constraints, the problem has a unique optimal weight vector. The full-sample result is:

| Index | GMV weight |
| --- | ---: |
| ASA52 | 0.0000% |
| NDDLWI | 0.0000% |
| NDLEEGF | 0.0000% |
| RDAU | 0.0000% |
| FDCIISAH | 0.0000% |
| HEDGNAV | 16.7665% |
| BACM0 | 15.4379% |
| H03432AU | 17.7956% |
| BAUBIL | 50.0000% |

**Annualised expected return: 3.940%.**

**Annualised volatility: 1.383%.**

Weights sum to 100% before rounding. Displayed zero weights are zero within numerical precision.

### Interpretation

BAUBIL reaches its 50% limit. The remaining allocation is split between HEDGNAV, BACM0 and H03432AU to minimise joint portfolio variance. The model does not require every index to be held.

Compared with uncapped GMV, the cap reduces the largest allocation from approximately 98.28% to 50%, while volatility rises from 0.554% to 1.383%. Expected return also changes from 3.329% to 3.940%.

GMV minimises estimated risk. It does not maximise return or identify a portfolio suitable for every investor. The growth/defensive and risk-aversion objectives in later questions address different investment needs.

The capped GMV results under alternative estimates are:

| Estimation period | GMV expected return | GMV volatility |
| --- | ---: | ---: |
| Full sample | 3.940% | 1.383% |
| Recent 10 years | 2.647% | 1.574% |
| Recent 5 years | 3.686% | 1.718% |

\newpage

## Q2(c): Minimum variance for target returns

### Problem and target range

We solve the same constrained problem as Q2(a), retaining the inequality $m^\top w$ $\geq$ $\mu$. The full-sample efficient interval is 3.9403% to 9.5866%. In addition to the 81-point frontier, we report requirements from 3% to 9.5% to show behaviour below GMV, intermediate trade-offs and a high-return allocation near the maximum.

The maximum is attained by allocating 50% to NDLEEGF and 50% to NDDLWI, the two highest estimated means. Requirements above 9.5866% are infeasible under the full-sample estimates and 50% cap.

### Full-sample results

| Return requirement | Achieved expected return | Volatility | Largest weight |
| --- | ---: | ---: | ---: |
| 3.00% | 3.940% | 1.383% | 50.00% |
| 4.00% | 4.000% | 1.413% | 50.00% |
| 5.00% | 5.000% | 2.882% | 34.55% |
| 6.00% | 6.000% | 4.546% | 29.37% |
| 7.00% | 7.000% | 6.310% | 39.64% |
| 8.00% | 8.000% | 8.186% | 50.00% |
| 9.00% | 9.000% | 10.340% | 50.00% |
| 9.50% | 9.500% | 11.500% | 50.00% |

At a 3% requirement, the return constraint is inactive because GMV already earns an estimated 3.940%. Forcing equality to 3% would solve a different problem. At the reported requirements above GMV's mean, the constraint binds and achieved expected return equals the requirement within numerical precision.

### Selected allocations

| Index | 4% requirement | 6% requirement | 8% requirement | 9.5% requirement |
| --- | ---: | ---: | ---: | ---: |
| ASA52 | 0.00% | 0.00% | 0.00% | 0.00% |
| NDDLWI | 0.00% | 0.00% | 4.80% | 26.54% |
| NDLEEGF | 0.00% | 4.83% | 16.44% | 22.51% |
| RDAU | 0.00% | 0.00% | 0.00% | 0.00% |
| FDCIISAH | 0.21% | 23.48% | 50.00% | 50.00% |
| HEDGNAV | 19.90% | 24.13% | 0.00% | 0.00% |
| BACM0 | 10.60% | 18.19% | 9.24% | 0.00% |
| H03432AU | 19.28% | 29.37% | 19.52% | 0.95% |
| BAUBIL | 50.00% | 0.00% | 0.00% | 0.00% |

At 4%, BAUBIL reaches its 50% cap. At 6%, no index reaches the cap, and the solution matches the uncapped portfolio at that requirement. At 8% and 9.5%, FDCIISAH reaches 50%, so additional expected return is obtained through other indices rather than increasing this holding further.

Estimated volatility rises as the required return rises. Covariances determine which combinations meet each requirement with minimum variance, and choosing only the highest-return index would neither respect the cap nor reproduce these efficient allocations.

\newpage

## Q2(d): Sensitivity to parameter estimates

### Comparison design and frontiers

We repeat the optimisation using the full 248-return sample, recent 120 returns and recent 60 returns from Q1. Constraints, annualisation and solver are unchanged. Each period uses its own expected-return vector and covariance matrix, so differences arise from parameter estimation.

![Figure 3. Efficient frontiers under the three Q1 estimation periods. The 50% curve is the main model in every panel; other caps and the uncapped model remain comparisons.](../figures/Q2a_window_frontiers.pdf)

For the 50%-capped model, annualised volatility at common requirements is:

| Estimation period | 4% volatility | 6% volatility | 8% volatility | Maximum expected return |
| --- | ---: | ---: | ---: | ---: |
| Full sample | 1.413% | 4.546% | 8.186% | 9.587% |
| Recent 10 years | 2.180% | 4.289% | 6.638% | 12.392% |
| Recent 5 years | 1.730% | 3.138% | 6.014% | 11.648% |

At an 8% requirement, fitted volatility changes from 8.186% to 6.638% and 6.014%. The maximum feasible expected return also changes. A lower fitted volatility under recent estimates does not establish lower future risk or a better estimation window, as each model evaluates portfolios using different estimated parameters.

\newpage

### Allocation sensitivity

The 8% allocations are:

| Index | Full sample | Recent ten years | Recent five years |
| --- | ---: | ---: | ---: |
| ASA52 | 0.00% | 0.00% | 0.00% |
| NDDLWI | 4.80% | 33.26% | 28.41% |
| NDLEEGF | 16.44% | 0.32% | 4.84% |
| RDAU | 0.00% | 0.00% | 0.00% |
| FDCIISAH | 50.00% | 0.00% | 0.00% |
| HEDGNAV | 0.00% | 50.00% | 50.00% |
| BACM0 | 9.24% | 0.00% | 0.00% |
| H03432AU | 19.52% | 0.00% | 0.00% |
| BAUBIL | 0.00% | 16.42% | 16.75% |

The full-sample portfolio allocates 50% to FDCIISAH and nothing to HEDGNAV. Both recent-window solutions allocate 50% to HEDGNAV and nothing to FDCIISAH. The cap prevents larger positions, but substantial changes in the composition remain.

We measure the difference from each full-sample allocation using:

$$
D(w,\widetilde w)=\frac12\sum_i|w_i-\widetilde w_i|.
$$

For long-only portfolios, D is the fraction of capital allocated differently, between zero and one. The following table expresses it as a percentage. It is not realised trading turnover: these are alternative estimates at the same end date.

| Comparison with full sample | GMV | 4% requirement | 6% requirement | 8% requirement |
| --- | ---: | ---: | ---: | ---: |
| Recent 10 years | 10.22% | 23.59% | 75.87% | 94.89% |
| Recent 5 years | 14.38% | 15.15% | 75.58% | 90.36% |

Mean-variance portfolios are sensitive to changes in estimated returns and covariances. The 50% cap controls maximum allocations, but it does not remove estimation uncertainty or make the optimal weights stable. Later bootstrap and out-of-sample analysis are needed to assess allocation reliability and realised outcomes.

## Numerical validation and conclusion

All 1,091 long-only solutions passed feasibility and optimality checks. The maximum primal constraint violation was approximately $1.02\times10^{-14}$. Frontier variances were non-decreasing and cap comparisons respected the expected feasible-set ordering. Signed portfolios passed analytical feasibility and stationarity checks. The numerical implementation uses analytic gradients and active-constraint refinement for the convex Markowitz problem.

Our main model is fully invested, long-only and capped at 50% per index. It enforces a stated concentration policy while retaining the uncapped portfolio as an efficiency benchmark. Its full-sample GMV has expected return 3.940% and volatility 1.383%, with higher return requirements increasing the fitted risk. Both the frontier and allocations change with the estimation period.

These are fitted historical comparisons. Q1's qualifications about currency comparability, index-return definitions and estimation uncertainty remain relevant. The results do not establish better future performance from imposing the cap.

For later questions, retain Q1's asset order and full-precision inputs with weights summing to one and lying between zero and 50%.
