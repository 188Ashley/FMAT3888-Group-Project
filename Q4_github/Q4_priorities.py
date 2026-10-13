"""Editorial priorities only; preserve all original Q4 numbers and analysis."""

def add_priorities(original):
    guide=r'''# Q4: priorities for the combined group report

**Priority 1 - Essential:** retain to answer Q4(a)-(c), justify the model and explain the conclusions. Keep all three parts represented.

**Priority 2 - Supporting evidence:** include after Priority 1 if space permits; otherwise summarise or move to an appendix.

**Priority 3 - Optional detail:** keep in the repository or appendix unless extra space is available.

These are editorial recommendations, not assessment marks. All calculations, numerical results and figures are unchanged. Section labels apply to the text and tables beneath them unless a separate figure or item label is shown.

| Item | Priority | Recommended treatment |
| --- | ---: | --- |
| Horizon, Q1 inputs, inherited constraints and utility objective | 1 | State briefly and explicitly. |
| Full normal-to-mean-variance derivation | 2 | Retain the resulting objective; shorten intermediate steps if needed. |
| Selected risk-aversion values and justification | 1 | Explain that these are preference scenarios. |
| Q4(a) allocations, expected returns, risk and interpretation | 1 | Retain the allocation and risk-return results. |
| Figure 1: risk-aversion chart and allocation heatmap | 2 | Visual support for the essential tables; avoid duplicating both if space is tight. |
| MC methods, sample sizes, repetitions and accuracy definitions | 1 | Give enough detail to explain and reproduce the comparison. |
| Log-sum-exp objective and gradient implementation details | 2 | Summarise numerical stability; full implementation can remain in code. |
| MC accuracy/runtime summary and benchmark comparison | 1 | Keep numerical evidence for both accuracy and computational cost. |
| Figure 2 and gamma-by-gamma MC comparison table | 2 | Additional detail after the aggregate comparison. |
| Joint historical resampling and re-estimation design | 1 | State that both m and C are re-estimated. |
| Bootstrap allocation uncertainty, numerical evidence and interpretation | 1 | Retain evidence of weight variability and what it means. |
| Figure 3: allocation uncertainty visualisation | 2 | Useful support; can replace a detailed table if equivalent information remains. |
| Moving-block bootstrap experiment and block-length table | 3 | Additional dependence sensitivity; keep a brief independence limitation even if omitted. |
| Replication-count check | 2 | Summarise unresolved percentile precision; full table can move to an appendix. |
| Conclusion and model/estimation limitations | 1 | Distinguish simulation error from historical uncertainty. |
| Detailed numerical certificates, coverage checklist and downstream handover | 3 | Keep a short validation statement; retain full details in the repository. |

The smallest complete Q4 contribution includes the model and gamma choices, optimal allocations and risk-return comparison, MC accuracy and time evidence, and bootstrap allocation uncertainty. Optional labels do not make any part of Q4(a)-(c) optional.

\newpage

'''
    text=original;changes=[]
    def change(a,b):
        nonlocal text
        assert a in text,a
        text=text.replace(a,b,1);changes.append((b,a))
    for title,p in [('## Model and modelling choices',1),('### Return horizon and utility',1),('### Choosing the risk-aversion range',1),('## Q4(a): Optimal portfolios under different risk aversion',1),('### Portfolio allocations',1),('## Q4(b): Numerical expected-utility optimisation',1),('### Monte Carlo implementation',1),('### Experimental choices and accuracy measures',1),('### Numerical accuracy and computational performance',1),('## Q4(c): Historical sampling uncertainty',1),('### Resampling design',1),('### Allocation stability across preferences',1),('### Replication-count check',2),('## Interpretation, validation and handover',1),('### Numerical checks',3),('### Assignment and checkpoint coverage',3)]:
        change(title,title+' [Priority '+str(p)+']')
    def note(anchor,label):change(anchor,'**'+label+'**\n\n'+anchor)
    note('With $W_0=1$','Priority 2 - Supporting derivation: retain the final utility objective even if these intermediate steps are shortened.')
    note('We minimise its monotone equivalent','Priority 2 - Supporting implementation detail: the stable numerical objective and gradient.')
    note('![Figure 1.','Priority 2 - Supporting figure: risk-aversion outcomes and allocation heatmap.')
    note('![Figure 2.','Priority 2 - Supporting figure: MC accuracy and runtime trends.')
    note('The scenario-level comparison at $N=100{,}000$ is:','Priority 2 - Supporting table: gamma-by-gamma MC results; retain the aggregate accuracy/time evidence above as Priority 1.')
    change('### Visual uncertainty and dependence sensitivity','### Visual uncertainty [Priority 2]')
    note('Ordinary row resampling treats months as independent.','Priority 3 - Optional block experiment. Keep the independence limitation as Priority 1.')
    note('Q5 can continue independently','Priority 3 - Optional handover detail for the combined report.')
    restored=text
    for new,old in reversed(changes):restored=restored.replace(new,old,1)
    assert restored==original,'A non-editorial change was introduced'
    return guide+text
