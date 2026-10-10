# FMAT3888 Q2: final code, report and handover

The agreed main model is fully invested, long-only, with a 50% cap on each index. The uncapped long-only model is the benchmark; 40%/30% caps and unrestricted signed weights are comparisons. The cap implements a chosen concentration policy, not a data-estimated optimal threshold.

## Quick start

Upload this **Q2_github folder** beside the group's existing project folders. All Q1 inputs required by Q2 are bundled, so the folder also runs on its own. Python 3.11 or later is recommended; the exact tested environment is recorded in `VALIDATION.md`.

From the repository root:

```sh
python -m pip install -r Q2_github/requirements.txt
python Q2_github/Q2_full_analysis.py
```

From inside Q2_github instead:

```sh
python -m pip install -r requirements.txt
python Q2_full_analysis.py
```

The default input directory is `inputs/Q1_exports`. Reruns write into `generated/`, preserving the submitted `report/`, `results/` and `figures/`. The generated report uses the revised prose with recalculated tables. Numerical results and Markdown do not require Pandoc or LaTeX.

To use the group's existing Q1 exports, override their location explicitly:

```sh
python Q2_github/Q2_full_analysis.py --q1-dir Q1_github
```

## Folder contents

| Path | Purpose |
| --- | --- |
| `Q2_full_analysis.py` | Q2(a)-(d) optimisation, validation, comparison tables and frontier figures |
| `report_template.py` | Revised report template with numerical tables generated from results |
| `compile_report.py` | Compile the provided LaTeX, or edited Markdown, without running optimisation |
| `requirements.txt` | Pinned Python packages used for the calculations |
| `report/` | Final user-edited PDF, LaTeX source, editable Markdown and layout header |
| `results/` | Full-precision inputs, constraints, allocations, frontiers and comparisons |
| `figures/` | Adopted frontier, alternative-constraint frontiers and estimation-window frontiers, in PNG/PDF |
| `inputs/Q1_exports/` | Original Q1 clean returns, parameter exports, results workbook, code, figures and run summary |
| `inputs/raw/Bloomber_data.xlsx` | Original data workbook used to produce Q1 inputs |
| `documents/` | Assignment instructions, APRA methodology and supplied method toolbox |
| `Groupmate_Summary.md` | Baseline decisions, data conventions and next-question handover |
| `DATA_DICTIONARY.md` | File meanings, units and asset-order conventions |
| `VALIDATION.md` | Fresh-folder rerun and comparison results |
| `FILE_SHA256.json` | Checksums for the packaged files |

## Read or edit the final report

The official final report is `report/Q2_Complete_Report.pdf`. Its editable wording is `report/Q2_Report_Editable.md`. The report covers Q2(a)-(d), including actual efficient-frontier plots.

With a LaTeX installation containing pdflatex, compile the supplied source:

```sh
python Q2_github/compile_report.py
```

After editing `report/Q2_Report_Editable.md`, install Pandoc as well and rebuild its LaTeX and PDF:

```sh
python Q2_github/compile_report.py --from-markdown
```

These commands intentionally update the final report. They do not change optimisation outputs. If you change inputs or constraints, recalculate first and update the report's narrative and figures accordingly; the editable report is a snapshot, not a live spreadsheet.

For a numerical rerun with additional cap comparisons:

```sh
python Q2_github/Q2_full_analysis.py --caps 0.4 0.3
```

`--caps` sets additional comparisons; it does not change the adopted 50% cap.

## Optional Q3 feasibility check

Once all nine APRA growth fractions have been verified, provide a CSV with columns `Asset,Growth_fraction`, using exact asset labels and decimal fractions in [0,1]:

```sh
python Q2_github/Q2_full_analysis.py --growth-classification verified_growth_fractions.csv
```

The script checks whether 30%, 70% and 90% growth exposure can be attained under the chosen bounds. No unverified classification is supplied as a baseline. This check does not solve Q3 itself.

## Reproduce Q1 from the raw workbook

From the repository root:

```sh
python Q2_github/inputs/Q1_exports/Q1_full_analysis.py --input Q2_github/inputs/raw/Bloomber_data.xlsx --output-dir Q2_github/generated/Q1_reproduced
python Q2_github/Q2_full_analysis.py --q1-dir Q2_github/generated/Q1_reproduced --output-dir Q2_github/generated/Q2_from_reproduced_Q1
```

Use explicit Q1 paths: its original code is included unchanged and retains its original defaults. Its original workbook/run-summary source paths are provenance from the earlier run, not required paths on your computer.

## GitHub upload

Unzip the archive and add the contained `Q2_github` folder to the group repository. Keep its subfolders intact. The `.gitignore` excludes temporary files and local reruns, while keeping the submitted results, figures and report. Existing Q1 files need not be replaced.
