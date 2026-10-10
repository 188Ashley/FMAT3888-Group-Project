# Package validation

Validated on 10 October 2026 with Python 3.12.14.

## Fresh standalone Q2 run

- Ran the packaged Q2 script using its bundled Q1 exports and a new output directory.
- All numerical content in the regenerated Q2_results.json matched the previously checked full-precision results exactly.
- All 1,091 long-only solutions passed feasibility and KKT optimality checks.
- Maximum primal constraint violation: 1.021405182655144e-14.
- KKT certificate tolerance: 1e-7; primal feasibility tolerance: 1e-8.
- Frontier monotonicity, nested feasible-set comparisons and below-GMV tests passed.
- Signed benchmarks passed their analytical feasibility and stationarity checks.
- Regenerated editable report text exactly matches the final edited report text.
- The final PDF is byte-identical to the reviewed eight-page final report; it is copied without modification.

## Raw-data reproduction

- Ran the original Q1 code against the included raw workbook, writing into a new directory.
- Reproduced all 248-by-9 monthly returns and baseline parameter CSV values with maximum numerical difference zero.
- The source workbook matches the original Q1 source SHA256.

## Environment

- numpy: 2.3.5
- pandas: 2.2.3
- scipy: 1.17.0
- matplotlib: 3.10.8
- openpyxl: 3.1.5
