# FMAT3888 Q4(a)-(c): final analysis and report

The folder completes Q4 using the current Q1 estimates and the agreed Q2 baseline. Q3 growth targets are not imposed in Q4, as confirmed by the supplied checkpoint. Existing Q1/Q2/Q3 files are not modified.

## Read first

- `report/Q4_Complete_Report.pdf`: final user-edited nine-page report, with derivation, results, numerical comparisons, historical uncertainty and requirements coverage.
- `report/Q4_Report_Editable.md`: editable/copy-paste report text.
- `Groupmate_Summary.md`: essential decisions and downstream handover.
- `results/Q4a_benchmark.csv`: exact fitted optimal weights for each risk-aversion value.
- `results/Q4_config_and_validation.json`: full-precision model, units, horizon, constraints, seeds and validation.

## Model and experimental settings

- Assets: the original nine-index order from Q1/Q2.
- Fully invested, long-only, 50% cap on every index; no growth-target equality.
- One-year normal arithmetic return model, with annualised mean = 12 x monthly mean and covariance = 12 x sample monthly covariance, ddof=1.
- Risk-aversion scenarios: 1, 5, 10, 25 and 100. These are preference sensitivity scenarios, not an estimated best gamma.
- Normal mean-variance objective: m.T x - gamma/2 x.T C x.
- Standard and antithetic MC: N = 1,000/10,000/100,000 total return vectors, eight independent replications; fixed samples within each optimisation.
- IID historical bootstrap: 10,000 resamples of 248 joint monthly rows. Re-estimate both moments in every sample.
- Dependence sensitivity: 6/12/24-month moving joint blocks, 1,000 resamples per length, with the same moment convention and objective.
- Random seed: 388804, independent SeedSequence streams for the three experiments.

## Reproduce

From the repository root, after unzipping this folder beside the other question folders:

```sh
python -m pip install -r Q4_github/requirements.txt
python Q4_github/Q4_full_analysis.py
python Q4_github/Q4_figures.py --output-dir Q4_github/generated
python Q4_github/Q4_report.py --output-dir Q4_github/generated
python Q4_github/Q4_verify.py --output-dir Q4_github/generated
```

Python 3.11 or later is recommended. The delivered run used Python 3.12.14; exact computational-package versions are pinned. Numerical reruns default to `generated/` and preserve the delivered `results/`, `figures/` and edited `report/`. The figures need Matplotlib; report-source generation additionally requires Pandoc. Numerical optimisation itself does not require Pandoc or LaTeX.

To compile the newly generated report, install a LaTeX distribution containing pdflatex:

```sh
python Q4_github/Q4_compile_report.py --report-dir Q4_github/generated/report
```

To compile the delivered LaTeX source without rerunning calculations:

```sh
python Q4_github/Q4_compile_report.py
```

To compile edits to the delivered Markdown (requires Pandoc and LaTeX):

```sh
python Q4_github/Q4_compile_report.py --from-markdown
```

`Q4_report.py` creates an automatic draft from saved result tables. Its wording precedes the user’s final edits. The authoritative final report is in report/. Do not regenerate over that edited report. The default numerical workflow writes to generated/ and preserves it. Recompiling edited Markdown does not update numerical results.

## Code contents

- `Q4_full_analysis.py`: independent Q1/Q2 reconciliation; constrained quadratic utility optimisation; direct empirical expected-utility optimisation; MC accuracy/runtime experiments; IID and moving-block bootstrap; parameter/weight distributions and validation exports.
- `Q4_figures.py`: four figures in PNG and vector PDF from the saved results.
- `Q4_report.py`: automatic analysis-draft generation from saved tables; this is the original numerical template, preceding the user’s final wording edits.
- `Q4_compile_report.py`: LaTeX compilation, optionally after Markdown edits.
- `Q4_verify.py`: independent checks of exported weights/moments, utility identities, the sampled objective gradient and bootstrap reconstruction.

## Main findings

Increasing risk aversion reduces fitted risk and return. Under the specified normal model, the quadratic benchmark is faster and exact; MC approximates it, with antithetic sampling improving aggregate accuracy in the tested experiment. Historical allocation uncertainty is substantially larger than the residual simulation error, particularly for intermediate risk aversion. This conclusion persists under block resampling.

The normal model and annualisation remain assumptions. IID bootstrap ignores serial dependence; moving blocks retain only within-block dependence and do not correct the annual covariance convention. Weight percentile endpoints can be unstable near zero/cap point masses; the report provides the 5,000-versus-10,000 replication check rather than claiming universal convergence.

## GitHub use

Upload the complete `Q4_github` folder; preserve its subfolders. All Q4 inputs are bundled. Large individual historical/MC files use compressed NPZ format and can be loaded with `numpy.load`. Temporary LaTeX files, caches and local reruns are excluded from the archive and `.gitignore`. Timing values are machine-dependent even when numerical results are reproducible.

The numerical CLI permits custom settings for further investigation. The report generator checks that its default experimental design was used, rather than silently describing custom results with default settings; adapt its narrative for a changed design.

The final report includes the user’s edited wording and Priority 1/2/3 labels. `Q4_priorities.py` supplies labels for the automatic numerical draft; the final edited Markdown is maintained separately.

## Original material and provenance

- `original_material/Uploaded_Group_Repository_Q1_Q2_Q3.zip`: exact original uploaded repository, containing all supplied Q1/Q2/Q3 code, results, supporting documents and the Q4/Q5 checkpoint. Extract it separately if you want the complete upstream project snapshot.
- `original_material/Bloomber_data.xlsx`: original Bloomberg workbook from that repository, copied without changes.
- `original_material/Q1_full_analysis.py` and `Q3_full_analysis.py`: original upstream scripts, copied without changes. The Q3 script is a notebook-style export; it is not required to run Q4.
- `original_material/Q4_User_Edited_Input.pdf`: the user’s edited report supplied for final typesetting.
- `documents/`: assignment instructions, Q4/Q5 checkpoint, APRA methodology and supplied method toolbox.
- `report/Editorial_Notes.txt`: small equation/grammar clarifications made during final typesetting.

No lecture-note PDFs were provided in this source repository; the supplied method toolbox is included. Q4 calculations use the bundled inputs/ exports directly and do not require running upstream scripts.
