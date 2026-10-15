"""Locked FMAT3888 Q5(a)-(c): trailing estimation and fixed-weight OOS tests.

Run: python Q5_full_analysis.py [--input-dir PATH] [--output-dir PATH]
Only the output directory is written. Q1-Q3 scripts are never imported/executed.
"""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import shutil

import numpy as np
import pandas as pd
import scipy
from scipy.optimize import linprog, minimize
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ASSETS = ["ASA52 Index", "NDDLWI Index", "NDLEEGF Index", "RDAU Index",
          "FDCIISAH Index", "HEDGNAV Index", "BACM0 Index", "H03432AU Index", "BAUBIL Index"]
GROWTH = np.array([1, 1, 1, 1, 1, .5, 0, 0, 0], dtype=float)
TARGETS = {"Defensive": .30, "Balanced": .70, "Aggressive": .90}
BOUNDS = [(0, .5)] * 9
A_EQ = np.vstack([np.ones(9), GROWTH])
PRIMAL_TOL = 1e-8
GAP_TOL = 1e-8  # absolute annual variance, certified by convex linearisation
RELATIVE_GAP_TOL = 1e-6
COLORS = {"Defensive": "#2878a6", "Balanced": "#d48b16", "Aggressive": "#bc4749"}


def require(condition, message):
    if not bool(condition):
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_csv(df, path):
    df.to_csv(path, index=False, float_format="%.17g", lineterminator="\n")


def load_returns(input_dir):
    r = pd.read_csv(input_dir / "Q1_clean_monthly_returns.csv", index_col=0,
                    parse_dates=True, float_precision="round_trip")
    require(r.columns.tolist() == ASSETS, "Asset order must match locked Q1 order.")
    require(isinstance(r.index, pd.DatetimeIndex) and not r.index.hasnans,
            "Invalid date index.")
    require(r.index.is_unique and r.index.is_monotonic_increasing, "Duplicate/unsorted dates.")
    require(np.all(np.diff(r.index.to_period("M").asi8) == 1), "Missing/duplicate months.")
    require(r.shape == (248, 9) and str(r.index[0].date()) == "2006-01-31"
            and str(r.index[-1].date()) == "2026-08-31", "Unexpected locked data extent.")
    require(np.isfinite(r.to_numpy()).all() and (r.to_numpy() > -1).all(),
            "Missing/invalid simple returns; no filling or deletion allowed.")
    config = json.loads((input_dir / "Q2_baseline_config.json").read_text(encoding="utf-8"))
    require(config["asset_order"] == ASSETS, "Q2 asset order mismatch.")
    c = config["recommended_constraints"]
    require(c["sum_weights"] == 1 and c["lower_bounds"] == [0] * 9
            and c["upper_bounds"] == [.5] * 9 and c["short_selling"] is False,
            "Q2 constraints disagree with locked configuration.")
    # Q2 moments are intentionally not read or used in any rolling estimate.
    return r


def minimum_variance(covariance, target):
    """Reuse Q3's HiGHS feasible start + scaled SLSQP with analytic gradient."""
    b = np.array([1., target])
    start = linprog(np.zeros(9), A_eq=A_EQ, b_eq=b, bounds=BOUNDS, method="highs")
    require(start.success, f"Infeasible Growth target {target}: {start.message}")
    result = minimize(lambda w: 100 * (w @ covariance @ w), start.x,
                      jac=lambda w: 200 * covariance @ w, method="SLSQP", bounds=BOUNDS,
                      constraints=[{"type": "eq", "fun": lambda w: A_EQ @ w - b,
                                    "jac": lambda w: A_EQ}],
                      options={"ftol": 1e-12, "maxiter": 10000})
    require(result.success, f"SLSQP failed: {result.message}")
    w = result.x  # no clipping or renormalisation after optimisation
    equality_error = float(np.max(np.abs(A_EQ @ w - b)))
    bound_error = float(max(0., -w.min(), w.max() - .5))
    require(equality_error <= PRIMAL_TOL and bound_error <= PRIMAL_TOL,
            "Portfolio constraints fail.")
    # For convex f, f(w)-f(w*) <= grad f(w)'(w-v), where v minimises
    # the linearisation over the same polytope. This is a global gap certificate.
    gradient_scaled = 200 * covariance @ w
    certificate = linprog(gradient_scaled, A_eq=A_EQ, b_eq=b,
                          bounds=BOUNDS, method="highs",
                          options={"dual_feasibility_tolerance": 1e-9,
                                   "primal_feasibility_tolerance": 1e-9})
    require(certificate.success, "Optimality certificate LP failed.")
    gap = float(gradient_scaled @ (w - certificate.x) / 100)
    stationarity = float(np.max(np.abs(gradient_scaled -
        A_EQ.T @ certificate.eqlin.marginals - certificate.lower.marginals -
        certificate.upper.marginals)) / 100)
    complementary = float(max(np.max(np.abs(w * certificate.lower.marginals)),
                              np.max(np.abs((.5 - w) * certificate.upper.marginals))) / 100)
    relative_gap = max(0., gap) / float(w @ covariance @ w)
    require(-GAP_TOL <= gap <= GAP_TOL and relative_gap <= RELATIVE_GAP_TOL and stationarity <= GAP_TOL
            and complementary <= GAP_TOL,
            f"Numerical global optimality check fails: gap={gap:.3g}, "
            f"stationarity={stationarity:.3g}, complementarity={complementary:.3g}, G={target}.")
    return w, {"solver_success": bool(result.success), "solver_status": int(result.status),
               "solver_message": str(result.message), "iterations": int(result.nit),
               "weight_sum": float(w.sum()), "growth_exposure": float(GROWTH @ w),
               "minimum_weight": float(w.min()), "maximum_weight": float(w.max()),
               "equality_error": equality_error, "bound_error": bound_error,
               "global_variance_gap_bound": max(0., gap),
               "relative_global_variance_gap_bound": relative_gap,
               "dual_stationarity_error": stationarity,
               "complementarity_error": complementary}


def figures(monthly, stability, output):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(8.5, 4.7), layout="constrained")
    for name in TARGETS:
        s = monthly[monthly.Portfolio == name].sort_values("Date")
        dates = pd.to_datetime(["2015-12-31"] + s.Date.tolist())
        ax.plot(dates, np.r_[1., s.Linked_wealth], label=name, color=COLORS[name], lw=2)
    ax.set(title="Out-of-sample cumulative wealth, 2016–2025",
           ylabel="Wealth (initial investment = 1)", xlabel="Year")
    ax.grid(alpha=.2)
    ax.legend(loc="upper left", frameon=False)
    fig.get_layout_engine().set(rect=(0, .08, 1, .92))
    fig.text(.5, .015, "Monthly fixed-weight rebalancing; targets updated each December; transaction costs omitted.",
             ha="center", fontsize=8)
    for ext in ["png", "pdf"]:
        metadata = {"CreationDate": None, "ModDate": None} if ext == "pdf" else None
        fig.savefig(output / f"Q5_fig_oos_cumulative_wealth.{ext}", dpi=220, metadata=metadata)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8.5, 4.7), layout="constrained")
    for name in TARGETS:
        s = stability[stability.Portfolio == name]
        ax.plot(pd.to_datetime(s.T0).dt.year, s.Weight_change_half_L1,
                marker="o", lw=2, color=COLORS[name], label=name)
    ax.set(title="Changes in annual target weights", xlabel="New target-weight year",
           ylabel="Half-L1 change from preceding December")
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xticks(range(2016, 2025))
    ax.grid(alpha=.2)
    ax.legend(frameon=False)
    fig.get_layout_engine().set(rect=(0, .08, 1, .92))
    fig.text(.5, .015, "0.5 × sum of absolute target-weight changes; excludes drift and monthly rebalancing trades.",
             ha="center", fontsize=8)
    for ext in ["png", "pdf"]:
        metadata = {"CreationDate": None, "ModDate": None} if ext == "pdf" else None
        fig.savefig(output / f"Q5_fig_weight_stability.{ext}", dpi=220, metadata=metadata)
    plt.close(fig)


def main(input_dir, output_dir):
    input_dir, output_dir = input_dir.resolve(), output_dir.resolve()
    require(output_dir != input_dir and input_dir not in output_dir.parents,
            "Outputs must be outside the read-only input directory.")
    input_hashes = {p.name: sha256(p) for p in input_dir.iterdir() if p.is_file()}
    r = load_returns(input_dir)
    dirs = {name: output_dir / name for name in
            ["01_code", "02_results", "03_figures_tables", "04_Q6_HANDOFF", "05_documentation"]}
    for folder in dirs.values():
        folder.mkdir(parents=True, exist_ok=True)
    records = {k: [] for k in ["windows", "weights", "means", "covariances", "asset_returns",
                               "portfolio_returns", "performance", "stability", "validation"]}
    periods = r.index.to_period("M")
    used_months, previous = set(), {}
    for year in range(2015, 2025):
        t = pd.Period(f"{year}-12", freq="M")
        t0 = str(t.end_time.date())
        est = r.loc[(periods >= t - 59) & (periods <= t)]
        oos = r.loc[(periods > t) & (periods <= t + 12)]
        require(len(est) == 60 and len(oos) == 12, "Wrong estimation/OOS count.")
        require(est.index[-1].to_period("M") == t and oos.index[0].to_period("M") == t + 1,
                "Window boundary error.")
        require(est.index[-1] <= pd.Timestamp(t0) < oos.index[0], "Temporal look-ahead.")
        block_months = set(oos.index.to_period("M"))
        require(not used_months.intersection(block_months), "Overlapping OOS blocks.")
        used_months.update(block_months)
        m, c = est.mean().values * 12, est.cov(ddof=1).values * 12
        require(np.allclose(m, np.mean(est.values, axis=0) * 12, atol=1e-14, rtol=0)
                and np.allclose(c, np.cov(est.values, rowvar=False, ddof=1) * 12,
                                atol=1e-14, rtol=0), "Annualisation check fails.")
        eigenvalues = np.linalg.eigvalsh(c)
        require(np.isfinite(c).all() and np.max(abs(c-c.T)) <= 1e-12
                and eigenvalues.min() > 0, "Invalid/non-positive-definite covariance.")
        window = {"T0": t0, "Estimation_start": str(est.index[0].date()),
                  "Estimation_end": str(est.index[-1].date()), "Estimation_count": len(est),
                  "OOS_start": str(oos.index[0].date()), "OOS_end": str(oos.index[-1].date()),
                  "OOS_count": len(oos)}
        records["windows"].append(window)
        records["means"].append({"T0": t0, **dict(zip(ASSETS, m))})
        for asset, row in zip(ASSETS, c):
            records["covariances"].append({"T0": t0, "Row_asset": asset, **dict(zip(ASSETS, row))})
        for date, row in oos.iterrows():
            records["asset_returns"].append({"T0": t0, "Date": str(date.date()), **row.to_dict()})
        for name, target in TARGETS.items():
            w, check = minimum_variance(c, target)
            records["weights"].append({"T0": t0, "Portfolio": name,
                                        "Growth_target": target, **dict(zip(ASSETS, w))})
            records["validation"].append({"T0": t0, "Portfolio": name, **check,
                "covariance_min_eigenvalue": float(eigenvalues.min()),
                "covariance_condition_number": float(np.linalg.cond(c)), "PASS": True})
            pr = oos.values @ w
            require(np.allclose(pr, np.sum(oos.values * w, axis=1), atol=1e-14, rtol=0),
                    "Fixed-weight return alignment fails.")
            wealth = np.cumprod(1 + pr)
            recursive = [1.]
            for value in pr:
                recursive.append(recursive[-1] * (1 + value))
            require(np.allclose(wealth, recursive[1:], atol=1e-14, rtol=0), "Wealth check fails.")
            predicted_return = float(w @ m)
            predicted_vol = float(np.sqrt(w @ c @ w))
            realised_return = float(12 * pr.mean())
            realised_vol = float(np.sqrt(12) * pr.std(ddof=1))
            records["performance"].append({**window, "Portfolio": name, "Growth_target": target,
                "Predicted_annual_return": predicted_return,
                "Realised_annualised_return": realised_return,
                "Return_error_realised_minus_predicted": realised_return - predicted_return,
                "Predicted_annual_volatility": predicted_vol,
                "Realised_annualised_volatility": realised_vol,
                "Volatility_error_realised_minus_predicted": realised_vol - predicted_vol,
                "OOS_compounded_return": float(wealth[-1] - 1), "OOS_terminal_wealth": float(wealth[-1])})
            for date, ret, value in zip(oos.index, pr, wealth):
                records["portfolio_returns"].append({"T0": t0, "Portfolio": name,
                    "Date": str(date.date()), "Monthly_return": float(ret), "Block_wealth": float(value)})
            if name in previous:
                prior_t0, prior_w = previous[name]
                records["stability"].append({"Previous_T0": prior_t0, "T0": t0, "Portfolio": name,
                    "Weight_change_half_L1": float(.5 * np.sum(np.abs(w-prior_w))),
                    "Largest_absolute_asset_weight_change": float(np.max(np.abs(w-prior_w)))})
            previous[name] = (t0, w.copy())
    frames = {name: pd.DataFrame(rows) for name, rows in records.items()}
    perf, monthly = frames["performance"], frames["portfolio_returns"]
    for name in TARGETS:
        mask = monthly.Portfolio == name
        require(np.all(np.diff(pd.to_datetime(monthly.loc[mask, "Date"]).dt.to_period("M").array.asi8) == 1),
                "Linked OOS series has skipped/duplicate months.")
        monthly.loc[mask, "Linked_wealth"] = (1 + monthly.loc[mask, "Monthly_return"]).cumprod().values
    for metric, rank_name, ascending in [
        ("Realised_annualised_return", "Return_rank_highest_first", False),
        ("Realised_annualised_volatility", "Volatility_rank_lowest_first", True),
        ("OOS_compounded_return", "Compounded_return_rank_highest_first", False)]:
        perf[rank_name] = perf.groupby("T0")[metric].rank(method="min", ascending=ascending).astype(int)
    summary = []
    for name in TARGETS:
        s = perf[perf.Portfolio == name]
        p = monthly[monthly.Portfolio == name]
        st = frames["stability"].query("Portfolio == @name")
        summary.append({"Portfolio": name, "Growth_target": TARGETS[name], "Evaluation_periods": len(s),
            "Mean_predicted_annual_return": s.Predicted_annual_return.mean(),
            "Mean_realised_annualised_return": s.Realised_annualised_return.mean(),
            "Mean_return_error": s.Return_error_realised_minus_predicted.mean(),
            "Return_prediction_RMSE": np.sqrt(np.mean(s.Return_error_realised_minus_predicted ** 2)),
            "Mean_predicted_annual_volatility": s.Predicted_annual_volatility.mean(),
            "Mean_realised_annualised_volatility": s.Realised_annualised_volatility.mean(),
            "Mean_volatility_error": s.Volatility_error_realised_minus_predicted.mean(),
            "Volatility_prediction_RMSE": np.sqrt(np.mean(s.Volatility_error_realised_minus_predicted ** 2)),
            "Linked_2016_2025_terminal_wealth": p.Linked_wealth.iloc[-1],
            "Linked_2016_2025_compounded_return": p.Linked_wealth.iloc[-1] - 1,
            "Pooled_120m_annualised_volatility": p.Monthly_return.std(ddof=1) * np.sqrt(12),
            "Mean_weight_change_half_L1": st.Weight_change_half_L1.mean(),
            "Maximum_weight_change_half_L1": st.Weight_change_half_L1.max(),
            "Return_rank1_periods": int((s.Return_rank_highest_first == 1).sum()),
            "Volatility_rank1_periods": int((s.Volatility_rank_lowest_first == 1).sum()),
            "Compounded_return_rank1_periods": int((s.Compounded_return_rank_highest_first == 1).sum())})
    summary = pd.DataFrame(summary)
    # Retain complete block comparisons as well as the compact report-priority summary.
    for name, df in frames.items():
        save_csv(df, dirs["02_results"] / f"Q5_{name}.csv")
    save_csv(summary, dirs["02_results"] / "Q5_summary.csv")
    table_columns = ["Portfolio", "Mean_predicted_annual_return", "Mean_realised_annualised_return",
                     "Mean_return_error", "Mean_predicted_annual_volatility",
                     "Mean_realised_annualised_volatility", "Mean_volatility_error",
                     "Linked_2016_2025_terminal_wealth"]
    save_csv(summary[table_columns], dirs["03_figures_tables"] / "Q5_table_predicted_vs_realised.csv")
    figures(monthly, frames["stability"], dirs["03_figures_tables"])
    config = {"asset_order": ASSETS, "growth_fractions": GROWTH.tolist(), "targets": TARGETS,
        "estimation_months": 60, "oos_months": 12, "t0_years": list(range(2015, 2025)),
        "annualisation": {"mean_multiplier": 12, "covariance_multiplier": 12, "ddof": 1},
        "constraints": {"sum_weights": 1, "lower": 0, "upper": .5},
        "oos_strategy": "fixed-weight monthly rebalancing; annual target update; no transaction costs",
        "units": {"returns_means_volatility_weights": "decimal", "covariance": "annualised decimal return squared"},
        "solver": {"feasible_start": "HiGHS", "method": "SLSQP", "objective_scale": 100,
                   "ftol": 1e-12, "maxiter": 10000, "primal_tolerance": PRIMAL_TOL,
                   "global_variance_gap_tolerance": GAP_TOL,
                   "relative_global_variance_gap_tolerance": RELATIVE_GAP_TOL},
        "classification_assumption": "Q3 classifications retained retrospectively; full-sample statistical rationale is a potential look-ahead limitation"}
    handoff = dirs["04_Q6_HANDOFF"]
    for name in ["windows", "weights", "means", "covariances", "asset_returns", "portfolio_returns", "performance"]:
        shutil.copyfile(dirs["02_results"] / f"Q5_{name}.csv", handoff / f"Q5_{name}.csv")
    # Historical input is supplied for later Q6 estimation, not a Q6 method decision.
    save_csv(r.loc[r.index.to_period("M") <= pd.Period("2025-12", freq="M")].reset_index(),
             handoff / "Q1_historical_monthly_returns_through_2025.csv")
    (handoff / "Q5_configuration.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    write_docs(dirs, config, summary, frames, input_dir)
    require(input_hashes == {p.name: sha256(p) for p in input_dir.iterdir() if p.is_file()},
            "Input files changed during execution.")
    require(len(perf) == 30 and len(monthly) == 360 and len(frames["asset_returns"]) == 120
            and len(frames["covariances"]) == 90 and len(frames["stability"]) == 27,
            "Incomplete output row counts.")
    for folder in dirs.values():
        for file in folder.iterdir():
            require(file.stat().st_size > 0, f"Empty output: {file}")
            if file.suffix == ".csv":
                saved = pd.read_csv(file, float_precision="round_trip")
                require(not saved.isna().any().any(), f"Missing exported value: {file}")
    validation = {"status": "PASS", "optimisations": 30, "windows": 10,
        "historical_window_count": 60, "oos_window_count": 12, "oos_unique_months": 120,
        "max_equality_error": float(frames["validation"].equality_error.max()),
        "max_bound_error": float(frames["validation"].bound_error.max()),
        "max_global_variance_gap_bound": float(frames["validation"].global_variance_gap_bound.max()),
        "max_relative_global_variance_gap_bound": float(frames["validation"].relative_global_variance_gap_bound.max()),
        "input_unchanged": True, "input_sha256": input_hashes,
        "code_sha256": sha256(Path(__file__)),
        "versions": {"python": platform.python_version(), "numpy": np.__version__,
                     "pandas": pd.__version__, "scipy": scipy.__version__, "matplotlib": matplotlib.__version__},
        "checks": ["60/12 month counts", "December included; OOS starts January", "no temporal overlap",
                   "no full-sample moments used", "exact asset order", "annualisation cross-check",
                   "solver success and bounds/equalities", "convex global optimality certificate",
                   "fixed-weight returns", "recursive wealth cross-check", "nonempty exports and no missing CSV cells"]}
    (dirs["05_documentation"] / "Q5_validation_summary.json").write_text(
        json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    manifest = [{"File": str(p.relative_to(output_dir)).replace("\\", "/"),
                 "Bytes": p.stat().st_size, "SHA256": sha256(p)}
                for p in sorted(output_dir.rglob("*")) if p.is_file()
                and p.name != "Q5_output_manifest.csv"]
    save_csv(pd.DataFrame(manifest), dirs["05_documentation"] / "Q5_output_manifest.csv")
    print(summary.to_string(index=False))
    print("PASS: 30 optimisations, 10 windows, 120 non-overlapping OOS months.")


def write_docs(dirs, config, summary, frames, input_dir):
    docs = dirs["05_documentation"]
    docs.joinpath("README_Q5.md").write_text(f"""# FMAT3888 Q5(a)–(c)

Executable: `01_code/Q5_full_analysis.py` (Python with NumPy, pandas, SciPy, Matplotlib).
From any directory: `python PATH/01_code/Q5_full_analysis.py`.
Defaults are resolved from the script location, not the current working directory.
Optional `--input-dir` and `--output-dir` select read-only inputs and a separate output folder.
Input: `{input_dir}`. No Q1–Q3 scripts execute or change.

## Files
- 02_results: windows (10); weights (30); means (10); covariance rows (90);
  asset returns (120); portfolio returns (360); performance (30, including ranks);
  stability (27 consecutive-date comparisons); validation (30 solver certificates);
  summary (3 portfolio rows with prediction errors, rankings and stability).
- 03_figures_tables: compact predicted/realised summary CSV; wealth and stability PNG/PDF figures.
- 04_Q6_HANDOFF: self-contained benchmark inputs, configuration and README.
- 05_documentation: this guide; methodology/assumptions; report-ready findings;
  validation JSON; SHA256/size output manifest (excludes itself).

All rate, volatility, exposure and weight fields are decimal fractions. Multiply by 100
for percentages. Covariance is annualised decimal return squared. Dates are ISO format.
The summary is the mean across ten annual tests; mean within-block volatility differs
from pooled 120-month volatility. Mean arithmetic annual return is not CAGR.
`OOS_compounded_return` is each 12-month block's compound return.
`Block_wealth` resets to 1 at every T0; `Linked_wealth` compounds all 120 OOS months,
with new target weights at each December boundary. It is an annually updated sequence
of SAA benchmarks, not a single unchanged ten-year weight vector.

## Validation and reproducibility
Every optimisation must pass explicit tolerances; failure stops execution.
The convex linearisation gap bounds annual variance suboptimality by 1e-8 absolute
and 1e-6 relative (one part per million). The largest observed absolute gap is recorded.
Constraint residuals must be at most 1e-8; dual stationarity and complementarity at most 1e-8.
Q3's positive objective scaling is retained. Weights are not clipped or renormalised.
Input SHA256 hashes and software versions are recorded in Q5_validation_summary.json.
No random simulation is used. Same code, data and software yield deterministic outputs;
solver results across software versions may differ slightly within tolerances.
""", encoding="utf-8")
    docs.joinpath("Q5_methodology_assumptions.md").write_text("""# Methodology and assumptions

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
""", encoding="utf-8")
    handoff = dirs["04_Q6_HANDOFF"]
    handoff.joinpath("README_Q6.md").write_text("""# Q6 fixed-SAA input interface (Q6 is not solved)

This folder is self-contained for consuming Q5 benchmark inputs.
All ISO dates and asset orders are exact; weights/means/returns/volatility are decimals.
Q5_configuration.json specifies exact asset order, Growth fractions, targets, constraints,
windows, annualisation, solver settings and retrospective classification assumption.

| File | Contents / units |
|---|---|
| Q5_windows.csv | 10 T0 calendar cutoffs, actual estimation/OOS endpoints, 60/12 counts |
| Q5_weights.csv | 30 dated labelled weight vectors; nine asset columns in exact Q1 order |
| Q5_means.csv | 10 dated vectors m; annualised arithmetic decimal returns |
| Q5_covariances.csv | 90 rows: T0, Row_asset and nine ordered columns; C in annualised decimal return squared |
| Q5_asset_returns.csv | 120 dated OOS asset return vectors, with originating T0; monthly simple decimals |
| Q5_portfolio_returns.csv | 360 dated portfolio returns, T0/label, Block_wealth, Linked_wealth |
| Q5_performance.csv | 30 dated predicted/realised return-risk comparisons, compound returns, rankings |
| Q1_historical_monthly_returns_through_2025.csv | 240 historical asset-return rows, January 2006–December 2025; for historical input availability |

Q5 uses fixed-weight monthly rebalancing within each 12-month block, no intra-block
re-optimisation and zero transaction costs. For the corresponding Q6 fixed benchmark,
select the agreed SAA label and T0, retrieve its weights and compare on that block's exact
dates. Do not update the fixed benchmark with tactical decisions. Keep units, annualisation,
Growth definitions and exposure limits consistent. Select only information dated at or before
each Q6 decision cutoff from the historical file; later rows are not available at earlier cutoffs.
This folder does not specify tactical rebalancing dates, gamma, deviation bounds or forecasts.

Join weights/metrics on (T0, Portfolio); join means/covariance/windows/asset returns on T0.
Reconstruct C with Row_asset in configuration asset order. Do not assume alphabetical order.
Block_wealth resets to 1 at T0; Linked_wealth is the annually updated 2016–2025 sequence,
not a single fixed long-term SAA weight vector. Compare only matched horizons.
The summary/figures are presentation aids; use these unrounded CSV inputs for Q6.
Growth classifications have a retrospective full-sample rationale, an acknowledged potential
look-ahead limitation. Publication lags, currency and total-return definitions are unverified.
The source and validation records are in ../01_code and ../05_documentation.
""", encoding="utf-8")
    lines = ["# Report-ready Q5 findings", "", "All percentages below are decimal rates multiplied by 100.",
             "The table averages ten annual test periods; the wealth figure links the 120 OOS months.",
             "", "## Q5(a): estimated portfolios"]
    for name in TARGETS:
        ws = frames["weights"].query("Portfolio == @name")
        ps = frames["performance"].query("Portfolio == @name")
        top = ws[ASSETS].mean().nlargest(3)
        lines.append(f"- {name}: three largest average target holdings: " +
                     ", ".join(f"{asset} {value:.2%}" for asset, value in top.items()) +
                     f". Predicted annual return range {ps.Predicted_annual_return.min():.2%}–"
                     f"{ps.Predicted_annual_return.max():.2%}; predicted volatility range "
                     f"{ps.Predicted_annual_volatility.min():.2%}–{ps.Predicted_annual_volatility.max():.2%}.")
    lines += ["", "## Q5(b)–(c): performance and stability"]
    for row in summary.itertuples():
        lines.append(f"- {row.Portfolio}: mean predicted/realised arithmetic annual return "
            f"{row.Mean_predicted_annual_return:.2%}/{row.Mean_realised_annualised_return:.2%}; "
            f"mean predicted/realised annual volatility {row.Mean_predicted_annual_volatility:.2%}/"
            f"{row.Mean_realised_annualised_volatility:.2%}. Mean return error "
            f"{100*row.Mean_return_error:.2f} percentage points; volatility error "
            f"{100*row.Mean_volatility_error:.2f} percentage points. Linked terminal wealth "
            f"{row.Linked_2016_2025_terminal_wealth:.4f}; ten-year compound return "
            f"{row.Linked_2016_2025_compounded_return:.2%}. Return rank 1 in "
            f"{row.Return_rank1_periods}/10 years; lowest volatility in {row.Volatility_rank1_periods}/10.")
        lines.append(f"  Mean/max half-L1 target-weight change: {row.Mean_weight_change_half_L1:.2%}/"
                     f"{row.Maximum_weight_change_half_L1:.2%} across nine transitions.")
    perf = frames["performance"]
    worst = perf.loc[perf.Return_error_realised_minus_predicted.abs().idxmax()]
    st = frames["stability"].loc[frames["stability"].Weight_change_half_L1.idxmax()]
    lines += ["", f"Largest absolute return prediction error: {worst.Portfolio}, T0={worst.T0}, "
        f"realised minus predicted {100*worst.Return_error_realised_minus_predicted:.2f} percentage points.",
        f"Largest target-weight change: {st.Portfolio}, {st.Previous_T0} to {st.T0}, "
        f"half-L1={st.Weight_change_half_L1:.2%}.", "", "## Annual OOS comparison"]
    for t0, s in perf.groupby("T0", sort=True):
        best = s.loc[s.Realised_annualised_return.idxmax()]
        low = s.loc[s.Realised_annualised_volatility.idxmin()]
        lines.append(f"- OOS {pd.Timestamp(t0).year+1}: highest arithmetic return "
            f"{best.Portfolio} ({best.Realised_annualised_return:.2%}); lowest volatility "
            f"{low.Portfolio} ({low.Realised_annualised_volatility:.2%}).")
    lines += ["", "These are descriptive historical comparisons. Rankings may differ by return definition;",
        "complete compounded-return rankings are in Q5_performance.csv. Realised performance",
        "varies across years, and predicted/realised gaps show that trailing estimates are uncertain.",
        "The wealth chart links annually updated targets; individual block target weights remain fixed.",
        "The classification look-ahead caveat, short realised volatility samples and zero-cost",
        "rebalancing assumption qualify these findings; no future superiority is established."]
    docs.joinpath("Q5_report_ready_findings.md").write_text("\n".join(lines)+"\n", encoding="utf-8")


if __name__ == "__main__":
    base = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=base.parent / "codex_input")
    parser.add_argument("--output-dir", type=Path, default=base)
    args = parser.parse_args()
    main(args.input_dir, args.output_dir)
