"""One editable Markdown source generates the matching Q2 LaTeX report."""
from pathlib import Path
import numpy as np
import subprocess,shutil

def write_report(results,directory):
    root=Path(directory).resolve();report=root/'report';report.mkdir(parents=True,exist_ok=True)
    models=results['models'];assets=results['assets'];base='Baseline: 50% cap';full=models['Full sample'];b=full['cases'][base];caps=results['comparison_caps']
    def pct(x,d=3):
        if abs(x)<5e-12:x=0.
        return f'{100*x:.{d}f}%'
    def tab(headers,rows):
        return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']+['---:']*(len(headers)-1))+' |\n'+'\n'.join('| '+' | '.join(row)+' |' for row in rows)
    params=tab(['Index','Annualised expected return','Annualised volatility'],[[a.replace(' Index',''),pct(full['mean'][i]),pct(np.sqrt(full['covariance'][i][i]))] for i,a in enumerate(assets)])
    samples=tab(['Estimation period','Returns','First return','Last return'],[[name,str(m['n_returns']),m['start'],m['end']] for name,m in models.items()])
    capsrows=tab(['Estimation period','Uncapped','50% cap']+[f'{100*c:g}% cap' for c in caps],[[name,pct(m['cases']['Uncapped benchmark']['selected_targets']['0.08']['volatility']),pct(m['cases'][base]['selected_targets']['0.08']['volatility'])]+[pct(m['cases'][f'Comparison: {c:.0%} cap']['selected_targets']['0.08']['volatility']) for c in caps] for name,m in models.items()])
    signedrows=tab(['Estimation period','Uncapped long-only volatility','Unrestricted volatility','Gross exposure'],[[name,pct(m['cases']['Uncapped benchmark']['selected_targets']['0.08']['volatility']),pct(m['unrestricted_signed']['selected_targets']['0.08']['volatility']),pct(m['unrestricted_signed']['selected_targets']['0.08']['gross_exposure'],2)] for name,m in models.items()])
    gmvweights=tab(['Index','GMV weight'],[[a.replace(' Index',''),pct(b['gmv']['weights'][i],4)] for i,a in enumerate(assets)])
    gmvwindows=tab(['Estimation period','GMV expected return','GMV volatility'],[[name,pct(m['cases'][base]['gmv']['expected_return']),pct(m['cases'][base]['gmv']['volatility'])] for name,m in models.items()])
    targets=tab(['Return requirement','Achieved expected return','Volatility','Largest weight'],[[pct(float(k),2),pct(p['expected_return']),pct(p['volatility']),pct(max(p['weights']),2)] for k,p in b['selected_targets'].items()])
    weights=tab(['Index','4% requirement','6% requirement','8% requirement','9.5% requirement'],[[a.replace(' Index','')]+[pct(b['selected_targets'][k]['weights'][i],2) for k in ['0.04','0.06','0.08','0.095']] for i,a in enumerate(assets)])
    riskstable=tab(['Estimation period','4% volatility','6% volatility','8% volatility','Maximum expected return'],[[name]+[pct(m['cases'][base]['selected_targets'][k]['volatility']) for k in ['0.04','0.06','0.08']]+[pct(m['cases'][base]['maximum_return'])] for name,m in models.items()])
    alloc8=tab(['Index','Full sample','Recent ten years','Recent five years'],[[a.replace(' Index','')]+[pct(m['cases'][base]['selected_targets']['0.08']['weights'][i],2) for m in models.values()] for i,a in enumerate(assets)])
    distances=[]
    for name,m in models.items():
        if name=='Full sample':continue
        out=[name]
        for key in ['GMV','0.04','0.06','0.08']:
            p=m['cases'][base]['gmv'] if key=='GMV' else m['cases'][base]['selected_targets'][key]
            ref=b['gmv'] if key=='GMV' else b['selected_targets'][key]
            out.append(pct(.5*abs(np.array(p['weights'])-ref['weights']).sum(),2))
        distances.append(out)
    dist=tab(['Comparison with full sample','GMV','4% requirement','6% requirement','8% requirement'],distances)
    residual=results['verification']['maximum_primal_residual']
    text=r'''# Question 2: Static Portfolio Optimisation

## Overview and inputs

We use the expected-return vector m and covariance matrix C from Q1 to construct portfolios, subject to full investment, no short selling and a 50% limit on each index. The uncapped long-only portfolio is used as a benchmark for comparison of different index caps; 40% and 30% caps and unrestricted signed weights are alternative comparisons.

The analysis answers all four parts of Q2: constraints and efficient-frontier plots; the global minimum-variance portfolio; portfolios for a range of return requirements; and sensitivity to alternative Q1 estimates.

Q1 provides 248 simple monthly returns from 31 January 2006 to 31 August 2026, calculated from 249 common monthly index levels. Each index uses the same dates. We retain Q1's annualisation: m equals 12 times the average monthly return, and C equals 12 times the sample monthly covariance matrix, using denominator N - 1. These are annualised arithmetic estimates, not compound annual growth rates.

__PARAMS__

For sensitivity analysis, we use the following Q1 estimation periods:

__SAMPLES__

The exported means and covariance matrices agree with calculations from the clean returns to floating-point precision. All three covariance matrices are positive definite. Calculations use full precision; the report rounds percentages for presentation. The methods are drawn from the supplied toolbox: Markowitz mean-variance optimisation, minimum-variance portfolios, efficient frontiers and restricted/unrestricted optimisation.

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

### Finding and plotting the efficient frontier

For each annual expected-return requirement μ, we solve:

$$
\min_w\;w^\top Cw
\quad\text{subject to}\quad
m^\top w\geq\mu,\quad\mathbf1^\top w=1,\quad0\leq w_i\leq0.50.
$$

Portfolio expected return is mᵀw and volatility is √(wᵀCw). We first find GMV without a return requirement and then maximise expected return under the same weight bounds. The full-sample efficient branch runs from **3.9403% to 9.5866% expected return**. We solve 81 requirements across this interval and plot achieved expected return against volatility. The point count controls plotting resolution.

![Figure 1. Full-sample efficient frontier for the adopted long-only, 50%-capped model. The marked GMV endpoint has expected return 3.940% and volatility 1.383%.](../figures/Q2_baseline_frontier.png)

Requirements below the GMV mean produce the same GMV portfolio; requirements above the maximum are infeasible. The figure shows the efficient branch, not the dominated lower-return branch.

### Comparison with alternative constraints

At the same 8% expected-return requirement, annualised volatility is:

__CAPS__

Compared with the uncapped portfolio, the 50%, 40% and 30% caps produce higher fitted volatility, with the increase becoming larger as the cap becomes more restrictive. We accept the increase under the 50% cap in exchange for limiting capital concentration in individual indices. This spreads capital across at least two indices, although it does not ensure that risk is evenly distributed.

The 50% cap increases volatility relative to the uncapped benchmark by approximately **0.024, 0.100 and 0.612 percentage points**, respectively. Its cost is small in the full sample but larger over five years. Tighter caps reduce the feasible set further and cannot lower minimum variance at a common feasible requirement.

We accept this efficiency cost to enforce the stated concentration policy. We do not claim that 50% is economically optimal or that the capped portfolio must outperform the benchmark.

To examine short selling separately, we compare uncapped long-only and unrestricted signed-weight portfolios at an 8% requirement:

__SIGNED__

The unrestricted portfolios have no gross-exposure limit and omit borrowing and financing costs. Their lower fitted volatility comes with large offsetting positions.

![Figure 2. Full-sample comparisons of index caps and short-selling assumptions. The uncapped long-only curve separates the effect of the cap from the effect of permitting signed weights.](../figures/Q2a_alternative_frontiers.png)

## Q2(b): Global minimum-variance portfolio

### Optimisation and allocation

The GMV portfolio solves:

$$
\min_w\;w^\top Cw
\quad\text{subject to}\quad
\mathbf1^\top w=1,\quad0\leq w_i\leq0.50.
$$

There is no expected-return requirement. With positive-definite C and linear constraints, the problem has a unique optimal weight vector. The full-sample result is:

__GMVWEIGHTS__

**Annualised expected return: 3.940%.**

**Annualised volatility: 1.383%.**

Weights sum to 100% before rounding. Displayed zero weights are zero within numerical precision.

### Interpretation

BAUBIL reaches its 50% limit. The remaining allocation is split between HEDGNAV, BACM0 and H03432AU to minimise joint portfolio variance. The model does not require every index to be held.

Compared with uncapped GMV, the cap reduces the largest allocation from approximately 98.28% to 50%, while volatility rises from 0.554% to 1.383%. Expected return also changes from 3.329% to 3.940%.

GMV minimises estimated risk. It does not maximise return or identify a portfolio suitable for every investor. The growth/defensive and risk-aversion objectives in later questions address different investment needs.

The capped GMV results under alternative estimates are:

__GMVWINDOWS__

## Q2(c): Minimum variance for target returns

### Problem and target range

We solve the same constrained problem as Q2(a), retaining the inequality mᵀw ≥ μ. The full-sample efficient interval is 3.9403% to 9.5866%. In addition to the 81-point frontier, we report requirements from 3% to 9.5% to show behaviour below GMV, intermediate trade-offs and a high-return allocation near the maximum.

The maximum is attained by allocating 50% to NDLEEGF and 50% to NDDLWI, the two highest estimated means. Requirements above 9.5866% are infeasible under the full-sample estimates and 50% cap.

### Full-sample results

__TARGETS__

At a 3% requirement, the return constraint is inactive because GMV already earns an estimated 3.940%. Forcing equality to 3% would solve a different problem. At the reported requirements above GMV's mean, the constraint binds and achieved expected return equals the requirement within numerical precision.

### Selected allocations

__WEIGHTS__

At 4%, BAUBIL reaches its 50% cap. At 6%, no index reaches the cap, and the solution matches the uncapped portfolio at that requirement. At 8% and 9.5%, FDCIISAH reaches 50%, so additional expected return is obtained through other indices rather than increasing this holding further.

Estimated volatility rises as the required return rises. Covariances determine which combinations meet each requirement with minimum variance, and choosing only the highest-return index would neither respect the cap nor reproduce these efficient allocations.

## Q2(d): Sensitivity to parameter estimates

### Comparison design and frontiers

We repeat the optimisation using the full 248-return sample, recent 120 returns and recent 60 returns from Q1. Constraints, annualisation and solver are unchanged. Each period uses its own expected-return vector and covariance matrix, so differences arise from parameter estimation.

![Figure 3. Efficient frontiers under the three Q1 estimation periods. The 50% curve is the main model in every panel; other caps and the uncapped model remain comparisons.](../figures/Q2a_window_frontiers.png)

For the 50%-capped model, annualised volatility at common requirements is:

__RISKS__

At an 8% requirement, fitted volatility changes from 8.186% to 6.638% and 6.014%. The maximum feasible expected return also changes. A lower fitted volatility under recent estimates does not establish lower future risk or a better estimation window, as each model evaluates portfolios using different estimated parameters.

### Allocation sensitivity

The 8% allocations are:

__ALLOC8__

The full-sample portfolio allocates 50% to FDCIISAH and nothing to HEDGNAV. Both recent-window solutions allocate 50% to HEDGNAV and nothing to FDCIISAH. The cap prevents larger positions, but substantial changes in the composition remain.

We measure the difference from each full-sample allocation using:

$$
D(w,\widetilde w)=\frac12\sum_i|w_i-\widetilde w_i|.
$$

For long-only portfolios, D is the fraction of capital allocated differently, between zero and one. The following table expresses it as a percentage. It is not realised trading turnover: these are alternative estimates at the same end date.

__DIST__

Mean-variance portfolios are sensitive to changes in estimated returns and covariances. The 50% cap controls maximum allocations, but it does not remove estimation uncertainty or make the optimal weights stable. Later bootstrap and out-of-sample analysis are needed to assess allocation reliability and realised outcomes.

## Numerical validation and conclusion

All __COUNT__ long-only solutions passed feasibility and optimality checks. The maximum primal constraint violation was approximately __RESIDUAL__. Frontier variances were non-decreasing and cap comparisons respected the expected feasible-set ordering. Signed portfolios passed analytical feasibility and stationarity checks. The numerical implementation uses analytic gradients and active-constraint refinement for the convex Markowitz problem.

Our main model is fully invested, long-only and capped at 50% per index. It enforces a stated concentration policy while retaining the uncapped portfolio as an efficiency benchmark. Its full-sample GMV has expected return 3.940% and volatility 1.383%, with higher return requirements increasing the fitted risk. Both the frontier and allocations change with the estimation period.

These are fitted historical comparisons. Q1's qualifications about currency comparability, index-return definitions and estimation uncertainty remain relevant. The results do not establish better future performance from imposing the cap.

For later questions, retain Q1's asset order and full-precision inputs with weights summing to one and lying between zero and 50%.
'''
    replacements={'PARAMS':params,'SAMPLES':samples,'CAPS':capsrows,'SIGNED':signedrows,'GMVWEIGHTS':gmvweights,'GMVWINDOWS':gmvwindows,'TARGETS':targets,'WEIGHTS':weights,'RISKS':riskstable,'ALLOC8':alloc8,'DIST':dist,'COUNT':format(results['verification']['solved_portfolios'], ','),'RESIDUAL':('$'+format(residual, '.2e').split('e')[0]+r'\times10^{'+str(int(format(residual, '.2e').split('e')[1]))+'}$')}
    for key,value in replacements.items():text=text.replace('__'+key+'__',value)
    # Unicode equations are convenient for editing; use math markup in the PDF source.
    text=text.replace('μ',r'$\mu$').replace('≥',r'$\geq$')
    text=text.replace('mᵀw',r'$m^\top w$').replace('√(wᵀCw)',r'$\sqrt{w^\top Cw}$')
    (report/'Q2_Report_Editable.md').write_text(text)
    pdftext=text.replace('.png)', '.pdf)')
    for heading in ['## Q2(a):','### Finding and plotting the efficient frontier','### Comparison with alternative constraints','## Q2(b):','## Q2(c):','## Q2(d):','### Allocation sensitivity']:
        pdftext=pdftext.replace(heading,'\\newpage\n\n'+heading)
    (report/'Q2_Report_PDF_Source.md').write_text(pdftext)
    header=r'''\usepackage{float}
\usepackage{fancyhdr}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small FMAT3888: Portfolio Construction}
\fancyhead[R]{\small Question 2(a)--(d)}
\fancyfoot[C]{\thepage}
\setlength{\headheight}{14pt}
\setlength{\parskip}{5pt}
'''
    (report/'header.tex').write_text(header)
    if shutil.which('pandoc'):
        subprocess.run(['pandoc','Q2_Report_PDF_Source.md','-s','-t','latex','-o','Q2_Complete_Report.tex','--include-in-header','header.tex','-V','geometry:margin=20mm','-V','fontsize:10pt','-V','papersize:a4','--resource-path','.' ],cwd=report,check=True)
        tex=report/'Q2_Complete_Report.tex'
        tex.write_text(tex.read_text().replace(r'\begin{figure}',r'\begin{figure}[H]'))
