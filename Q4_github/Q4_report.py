"""Build the Q4 editable report and LaTeX from saved results."""
from pathlib import Path
from Q4_priorities import add_priorities
import argparse,json,subprocess,re
import numpy as np,pandas as pd

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']+['---:']*(len(headers)-1))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rows])
def pct(v,d=3):return f'{100*v:.{d}f}%'
def main():
    here=Path(__file__).resolve().parent;p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,default=here);a=p.parse_args();root=a.output_dir;r=root/'results';report=root/'report';report.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((r/'Q4_config_and_validation.json').read_text());mv=pd.read_csv(r/'Q4a_benchmark.csv');mc=pd.read_csv(r/'Q4b_MC_runs.csv');summary=pd.read_csv(r/'Q4b_MC_summary.csv');boot=pd.read_csv(r/'Q4c_allocation_uncertainty.csv');stability=pd.read_csv(r/'Q4c_stability_summary.csv');conv=pd.read_csv(r/'Q4c_replication_convergence.csv');block=pd.read_csv(r/'Q4c_block_stability_summary.csv');assets=cfg['assets']
    if cfg['gammas']!=[1.,5.,10.,25.,100.] or cfg['mc_sizes']!=[1000,10000,100000] or cfg['mc_independent_repetitions']!=8 or cfg['bootstrap_repetitions']!=10000 or cfg['block_bootstrap']['lengths']!=[6,12,24] or cfg['block_bootstrap']['replications_per_length']!=1000:
        raise ValueError('This report template describes the default experiment. For custom settings, use numerical exports and adapt the narrative before generating a report.')
    trade=table(['Risk aversion','Expected return','Volatility','CE return'],[[f'{v.gamma:g}',pct(v.expected_return),pct(v.volatility),pct(v.certainty_equivalent_return)] for _,v in mv.iterrows()])
    weights=table(['Index']+[f'gamma = {g:g}' for g in mv.gamma],[[asset.replace(' Index','')]+[pct(v[asset],2) for _,v in mv.iterrows()] for asset in assets])
    pooled=mc.groupby(['method','N']).agg(distance=('half_L1_weight_error','mean'),regret=('true_CE_regret','mean'),seconds=('amortised_total_seconds','median')).reset_index()
    pooledtable=table(['Method','N','Mean distance','Mean CE loss (bp)','Median time (ms)'],[[v.method.replace(' MC',''),f'{v.N:,}',pct(v.distance,2),f'{10000*v.regret:.3f}',f'{1000*v.seconds:.2f}'] for _,v in pooled.iterrows()])
    comparison=[]
    for g in mv.gamma:
        standard=summary[(summary.gamma==g)&(summary.N==100000)&(summary.method=='Standard MC')].iloc[0]
        anti=summary[(summary.gamma==g)&(summary.N==100000)&(summary.method=='Antithetic MC')].iloc[0]
        comparison.append([f'{g:g}',pct(standard.mean_half_L1_weight_error,2),pct(anti.mean_half_L1_weight_error,2),f'{10000*standard.mean_true_CE_regret:.4f}',f'{10000*anti.mean_true_CE_regret:.4f}'])
    comptable=table(['Risk aversion','Standard distance','Antithetic distance','Standard loss (bp)','Antithetic loss (bp)'],comparison)
    timingratio=summary[(summary.N==100000)&(summary.method=='Antithetic MC')].sort_values('gamma').median_solver_seconds.to_numpy()/mv.sort_values('gamma').median_solver_seconds.to_numpy()
    stabletable=table(['Risk aversion','Median distance','95th percentile distance','Largest weight SD (pp)'],[[f'{v.gamma:g}',pct(v.median_half_L1,2),pct(v.p95_half_L1,2),f'{100*v.max_marginal_sd:.2f}'] for _,v in stability.iterrows()])
    g10=boot[boot.gamma==10];rangetable=table(['Index','Fitted weight','Bootstrap mean','2.5%','97.5%'],[[v.Asset.replace(' Index',''),pct(v.baseline_weight,2),pct(v.bootstrap_mean,2),pct(v.p2_5,2),pct(v.p97_5,2)] for _,v in g10.iterrows()])
    blocktable=table(['Risk aversion','IID months','6-month blocks','12-month blocks','24-month blocks'],[[f'{g:g}',pct(stability[stability.gamma==g].iloc[0].median_half_L1,2)]+[pct(block[(block.gamma==g)&(block.block_length==L)].iloc[0].median_half_L1,2) for L in [6,12,24]] for g in mv.gamma])
    convtable=table(['Risk aversion','Max mean-weight change (pp)','Max endpoint change (pp)'],[[f'{v.gamma:g}',f'{100*v.max_mean_weight_difference:.2f}',f'{100*v.max_percentile_endpoint_difference:.2f}'] for _,v in conv.iterrows()])
    s1=pooled[(pooled.method=='Standard MC')&(pooled.N==100000)].iloc[0];a1=pooled[(pooled.method=='Antithetic MC')&(pooled.N==100000)].iloc[0];g10s=stability[stability.gamma==10].iloc[0]
    text=r'''# Question 4: Utility, Monte Carlo and portfolio uncertainty

## Model and modelling choices

Q4 separates investor preferences, numerical approximation and historical estimation uncertainty. We first solve the normal-model utility problem exactly as a constrained mean-variance problem, then reproduce it using Monte Carlo, and finally resample the historical data to examine how much the optimal weights change.

The current Q1 exports provide 248 common monthly simple returns, dated 31 January 2006 to 31 August 2026, in the group's fixed nine-index order. We independently reconcile the annualised means and covariance with the current Q1 workbook and Q2 configuration. Our constraints remain

$$
\mathbf{1}^{\top}x=1,\qquad 0\le x_i\le0.50.
$$

The checkpoint specifies that Q4 does not impose Q3's 30%, 70% or 90% growth targets. No risk-free rate is needed for this utility objective. The 50% cap is inherited from Q2; it is not retuned using Q4 outcomes.

### Return horizon and utility

We use a **one-year normal arithmetic return model**, $R\sim N(m,C)$, with Q1's $m=12\bar R_{\mathrm{monthly}}$ and $C=12\widehat{\operatorname{Cov}}(R_{\mathrm{monthly}})$, using denominator $N-1$. This is an explicit modelling approximation, not a claim that compounded annual returns are normal or that multiplying monthly covariance by 12 incorporates serial dependence.

With $W_0=1$, $W_1=1+x^{\top}R$ and $U(W)=-\exp(-\gamma W)$, normality gives

$$
\mathbb E[U(W_1)]
=-\exp\!\left[-\gamma(1+x^{\top}m)+\frac{\gamma^2}{2}x^{\top}Cx\right].
$$

Thus maximising expected utility is equivalent to maximising

$$
f_\gamma(x)=x^{\top}m-\frac{\gamma}{2}x^{\top}Cx.
$$

The certainty-equivalent wealth is $1+f_\gamma(x)$: the certain wealth delivering the same utility. We report $f_\gamma(x)$ as the **certainty-equivalent return**. Utility levels across different $\gamma$ values are not comparable measures of performance because the preference functions differ.

### Choosing the risk-aversion range

We use $\gamma\in\{1,5,10,25,100\}$. A preliminary sweep from 0.01 to 250 shows that these choices span a return-oriented equity/infrastructure allocation, intermediate mixed portfolios, a cash-inclusive portfolio, and a solution close to GMV. They are illustrative preference scenarios, not estimates of an investor's preferences or a claim that one value is best. The preliminary sweep is retained in the results.

\newpage

## Q4(a): Optimal portfolios under different risk aversion

Because $C$ is positive definite and $\gamma>0$, the objective is strictly concave. Under the linear constraints each scenario has a unique optimum. We solve the corresponding convex minimisation using analytic gradients, refine the active-set solution and check feasibility and convex optimality.

__TRADE__

### Portfolio allocations

__WEIGHTS__

![Figure 1. The fitted risk-return choices and their capital allocations under increasing risk aversion. All scenarios use the same historical estimates and constraints.](../figures/Q4a_risk_aversion.png)

At $\gamma=1$, the optimal portfolio combines NDDLWI, NDLEEGF and a 50% holding in FDCIISAH. As risk aversion rises, lower-risk assets enter and both fitted return and volatility fall. At $\gamma=25$, BAUBIL receives about 44.75%; at $\gamma=100$, it reaches its 50% cap. The latter volatility, 1.398%, is close to capped GMV's 1.383%, but utility optimisation still rewards expected return and therefore does not return exactly the GMV weights.

The outcome follows the trade-off in $f_\gamma$: a larger $\gamma$ places more weight on variance. These are optimal portfolios conditional on the model, inputs and preference value, not universally optimal investment recommendations.

\newpage

## Q4(b): Numerical expected-utility optimisation

### Monte Carlo implementation

For each experiment we generate correlated normal return vectors using the Cholesky factor $L$ of $C$:

$$
R^{(k)}=m+LZ^{(k)},\qquad Z^{(k)}\sim N(0,I).
$$

The empirical expected utility is

$$
\widehat{\mathbb E[U(W_1)]}
=-e^{-\gamma}\frac1N\sum_{k=1}^{N}e^{-\gamma x^{\top}R^{(k)}}.
$$

We minimise its monotone equivalent

$$
h_N(x)=\frac1\gamma\log\!\left(\frac1N\sum_{k=1}^{N}e^{-\gamma x^{\top}R^{(k)}}\right),
$$

using log-sum-exp for numerical stability. Its gradient is the negative return mean under exponential weights. This solves the sampled expected-utility problem directly; it does not replace that problem with a sample mean-variance approximation.

Return draws remain fixed throughout each optimisation, making the objective smooth and reproducible. Each run starts from equal weights, rather than the exact benchmark. We compare standard MC with the toolbox's antithetic method, using pairs $m+LZ$ and $m-LZ$. The value of $N$ counts **total return vectors**, so antithetic MC uses $N/2$ independent pairs. Samples are shared across the five preference scenarios within an experiment, not redrawn at every solver evaluation.

### Experimental choices and accuracy measures

We test $N=1{,}000$, $10{,}000$ and $100{,}000$, with eight independent replications of each method and sample size. This tenfold ladder tests the accuracy-cost trade-off rather than selecting one unexplained simulation count. The fixed seed is 388804; separate child streams are used for MC, ordinary bootstrap and block bootstrap.

We measure allocation distance by

$$
D(x,\hat x)=\frac12\sum_i|x_i-\hat x_i|,
$$

which is the fraction of capital allocated differently. It is not realised trading turnover. We also evaluate each MC portfolio under the **exact original normal model**, using

$$
\Delta\mathrm{CE}=f_\gamma(x^*)-f_\gamma(\hat x)\ge0.
$$

This avoids judging the simulated portfolio only by its optimised in-sample utility. One basis point (bp) of CE return is $10^{-4}$. The exported results also report CE estimation error and relative expected-utility error at the fixed exact benchmark.

\newpage

### Numerical accuracy and computational performance

The following summaries give each risk-aversion scenario equal representation. Allocation distance and CE loss are means over the five scenarios and eight replications; timing is the median across those runs.

__POOLED__

![Figure 2. Allocation error and runtime as the number of simulated return vectors increases. Runtime includes optimisation plus an equal share of the one-time generation cost reused across preference scenarios.](../figures/Q4b_accuracy_runtime.png)

At $N=100{,}000$, mean allocation distance is __STANDARD_DISTANCE__ for standard MC and __ANTI_DISTANCE__ for antithetic MC. Mean exact-model CE loss is __STANDARD_REGRET__ bp and __ANTI_REGRET__ bp, respectively. Antithetic sampling improves these aggregate errors; it is not guaranteed to improve every finite-sample result.

The scenario-level comparison at $N=100{,}000$ is:

__MC_COMPARE__

Allocation error and economic objective error need not move together: nearby portfolios can have almost the same utility. Consequently both metrics are needed. For this experiment $N=100{,}000$ provides the most accurate tested aggregate approximation, at higher cost. Eight replications give a limited assessment of simulation variability, not a universal accuracy guarantee.

The exact quadratic benchmark takes approximately __MV_TIME_MIN__-__MV_TIME_MAX__ ms per solve. Antithetic MC at $N=100{,}000$ takes about __TIME_RATIO_MIN__-__TIME_RATIO_MAX__ times longer for the solver alone. Timings use one BLAS thread, exclude file input/output, and are machine-specific. The benchmark timing is the median of 30 solves per scenario; MC timings include genuine reoptimisation from equal weights.

For this normal/exponential-utility problem the mean-variance benchmark is preferable: it is both exact for the stated model and faster. MC is a validation exercise here and becomes more useful when such an analytical reduction is unavailable.

\newpage

## Q4(c): Historical sampling uncertainty

### Resampling design

The primary experiment resamples **248 complete monthly return rows with replacement**. All nine returns from a sampled month stay together, preserving their contemporaneous relationships. Each resample supplies a newly estimated monthly mean and sample covariance; we apply Q1's annualisation and reoptimise Q4(a) for every $\gamma$. We do not resample assets independently or hold the covariance fixed.

We use 10,000 IID resamples, following a smaller pilot in which some tail endpoints changed substantially. At this count the Monte Carlo standard error of an estimated selection probability is at most 0.5 percentage points, and each 2.5% tail contains about 250 observations. This does not imply that all weight percentiles are precise: constrained solutions have point masses at zero and the cap. We therefore check 5,000 versus 10,000 replications separately below.

The 2.5%-97.5% marginal ranges describe the resampled allocation distribution under the chosen scheme. They are not simultaneous portfolio confidence regions or future-return prediction intervals. Different marginal endpoints generally do not form a feasible portfolio when combined.

### Allocation stability across preferences

__STABILITY__

For $\gamma=10$, median allocation distance is __BOOT_G10_DISTANCE__, with a 95th percentile of __BOOT_G10_P95__. At $\gamma=100$, the median distance is much smaller, about 10.14%, although material uncertainty remains. Higher risk aversion is not uniformly more stable: the intermediate mixed portfolios also respond strongly to estimated means and covariances.

For $\gamma=10$, the marginal allocation ranges are:

__RANGES__

FDCIISAH's fitted weight is 33.35%, while H03432AU's is 24.92%; both have bootstrap ranges extending from zero to 50%. A zero fitted weight also need not imply that an asset is reliably excluded. This distinction between a unique fitted optimum and an uncertain estimated optimum is central to Q4(c).

\newpage

### Visual uncertainty and dependence sensitivity

![Figure 3. IID bootstrap allocation ranges for gamma = 10, and marginal allocation standard deviations across the preference scenarios. The dots show the original fitted allocation; the bands show resampling variability.](../figures/Q4c_bootstrap_uncertainty.png)

Ordinary row resampling treats months as independent. The observed lag-one autocorrelations are about 0.982 for BAUBIL and 0.219 for HEDGNAV, so independence is a material limitation. As a sensitivity check, we resample joint **moving blocks** of 6, 12 and 24 months: sample valid historical block starts uniformly, concatenate the blocks and truncate to 248 rows. This preserves dependence inside each block while retaining the same estimation and optimisation conventions.

Twelve months matches the stated model horizon; six and 24 months test shorter and longer dependence retention. These are transparent sensitivity choices, not an estimated optimal block length. Each length uses 1,000 replications, so block results are coarser than the primary IID experiment. This is an additional historical-bootstrap sensitivity check, not a replacement of the assignment's normal return model or Q1 covariance convention.

Median allocation distances are:

__BLOCK__

The intermediate allocations remain highly uncertain under every resampling scheme. For $\gamma=10$, the 12-month-block median distance is about 48.71%, close to the IID value. The schemes do not produce identical distributions; block resampling does not mechanically increase every uncertainty measure. Their agreement on substantial instability is more useful than treating a particular interval endpoint as exact.

### Replication-count check

Comparing the first 5,000 IID resamples with all 10,000 gives:

__CONVERGENCE__

The largest mean-weight change is about __MAX_MEAN_CHANGE__ percentage points. Some low-risk-aversion tail endpoints still move appreciably because of mixtures of zero, interior and capped allocations. In particular the largest endpoint change at $\gamma=1$ is about __G1_ENDPOINT_CHANGE__ percentage points. We report these ranges approximately and do not claim complete percentile convergence. More resamples would reduce simulation noise, but would not add historical information or eliminate model uncertainty.

\newpage

## Interpretation, validation and handover

Q4 identifies three distinct effects. Risk aversion changes the trade-off between fitted return and risk. Monte Carlo approximates a fixed normal-model optimum and introduces controllable simulation error. Historical resampling changes the estimated inputs and exposes much larger uncertainty in the resulting allocations. Increasing MC sample size cannot cure historical estimation uncertainty.

The 50% cap remains useful as the group's chosen capital-concentration policy, but does not stabilise all optimal weights. The results do not determine an investor's preferred $\gamma$, establish future outperformance or validate the normal model's tails. Q1's currency/index-definition qualifications and its arithmetic annualisation convention remain relevant. Block resampling addresses some within-block dependence in parameter uncertainty, not the assumption that the one-year covariance equals 12 times monthly covariance.

### Numerical checks

All __SOLUTION_COUNT__ primary benchmark, MC, IID-bootstrap and block-bootstrap solutions passed the stated checks. The largest constraint violation was __PRIMAL__ and the largest convex optimality-gap certificate was __GAP__, below the $10^{-7}$ threshold. Risk and expected return were non-increasing across the selected risk-aversion values. MC portfolios did not exceed the exact normal-model optimum when evaluated under the original parameters.

The normal utility formula, certainty-equivalent transformation and stable sampled objective were independently checked. All bootstrap covariance matrices were generated from complete joint samples using the same sample-covariance convention. Simulation seeds, timing conventions, bootstrap indices, parameter estimates, allocation distributions and representative simulated asset-return samples are retained with the code.

### Assignment and checkpoint coverage

| Requirement | Completed evidence |
| --- | --- |
| Q4(a): several risk-aversion choices; allocations, return and risk | Five scenarios, allocation table, risk-return table and Figure 1; design sweep retained. |
| Q4(b): numerical expected utility; benchmark, accuracy and performance | Standard/antithetic MC, three sample sizes, eight replications, exact-model CE losses, timing and Figure 2. |
| Q4(c): historical bootstrap and allocation reliability | Joint-row bootstrap, weight ranges and boundary frequencies, block sensitivity, replication check and Figure 3. |
| Checkpoint D2: retain model and reproducibility interface | m/C, horizon, constraints, gammas, seeds, samples, bootstrap indices/weights/moments and code exported. |

Q5 can continue independently using the Q3 strategic growth targets. Q6 must justify its own risk-aversion and tactical choices; Q4's five scenarios provide sensitivity evidence rather than an automatic value to inherit. Extension A can refer to the normal baseline and uncertainty results, while still requiring the original historical return matrix and its own risk-model investigation.

For the combined 8-10 page group report, prioritise the risk-aversion outcomes, a compact MC accuracy/time comparison and the bootstrap uncertainty conclusion. Keep the full simulation tables, diagnostic settings and block-length checks in an appendix or repository when space is limited.

**Sources:** supplied project instructions, Q4(a)-(c); supplied Q4/Q5 checkpoint; current Q1 exports and Q2 baseline in the uploaded group repository; supplied Method Toolbox. No short-selling ban or 50% cap is claimed to be imposed by the assignment itself.
'''
    repl={'TRADE':trade,'WEIGHTS':weights,'POOLED':pooledtable,'MC_COMPARE':comptable,'STABILITY':stabletable,'RANGES':rangetable,'BLOCK':blocktable,'CONVERGENCE':convtable,
          'STANDARD_DISTANCE':pct(s1.distance,2),'ANTI_DISTANCE':pct(a1.distance,2),'STANDARD_REGRET':f'{10000*s1.regret:.3f}','ANTI_REGRET':f'{10000*a1.regret:.3f}',
          'MV_TIME_MIN':f'{1000*mv.median_solver_seconds.min():.2f}','MV_TIME_MAX':f'{1000*mv.median_solver_seconds.max():.2f}',
          'TIME_RATIO_MIN':f'{timingratio.min():.0f}','TIME_RATIO_MAX':f'{timingratio.max():.0f}',
          'BOOT_G10_DISTANCE':pct(g10s.median_half_L1,2),'BOOT_G10_P95':pct(g10s.p95_half_L1,2),
          'MAX_MEAN_CHANGE':f'{100*conv.max_mean_weight_difference.max():.2f}','G1_ENDPOINT_CHANGE':f'{100*conv[conv.gamma==1].iloc[0].max_percentile_endpoint_difference:.2f}',
          'SOLUTION_COUNT':f"{cfg['validation']['checked_solutions']:,}",'PRIMAL':f"{cfg['validation']['maximum_primal_error']:.2e}",'GAP':f"{cfg['validation']['maximum_convex_optimality_gap']:.2e}"}
    for k,v in repl.items():text=text.replace('__'+k+'__',v)
    assert '__' not in text
    text=add_priorities(text)
    (report/'Q4_Report_Editable.md').write_text(text)
    (report/'Q4_Report_PDF_Source.md').write_text(re.sub(r'!\[Figure \d+\. ', '![' , text.replace('.png)', '.pdf)')))
    (report/'header.tex').write_text(r'''\usepackage{float}
\usepackage{fancyhdr}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small FMAT3888: Portfolio Construction}
\fancyhead[R]{\small Question 4(a)--(c)}
\fancyfoot[C]{\thepage}
\setlength{\headheight}{14pt}
\setlength{\parskip}{4pt}
''')
    subprocess.run(['pandoc','Q4_Report_PDF_Source.md','-s','-t','latex','-o','Q4_Complete_Report.tex','--include-in-header','header.tex','-V','geometry:margin=20mm','-V','fontsize:10pt','-V','papersize:a4','--resource-path','.'],cwd=report,check=True)
    tex=report/'Q4_Complete_Report.tex';tex.write_text(tex.read_text().replace(r'\begin{figure}',r'\begin{figure}[H]'))
if __name__=='__main__':main()
