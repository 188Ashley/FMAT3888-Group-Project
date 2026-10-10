#!/usr/bin/env python
# coding: utf-8

# In[1]:


import json
import numpy as np
import pandas as pd

from scipy.optimize import minimize, linprog


# In[2]:


# Load Q2 baseline configuration
with open("Q2_baseline_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

# Asset order used by Q2
assets = config["asset_order"]

# Load annualised expected returns from Q1
params = pd.read_excel(
    "Q1_results.xlsx",
    sheet_name="Q1c_Annualised_Parameters",
    header=3,
    index_col=0
)

# Load annualised covariance matrix from Q1
cov_df = pd.read_excel(
    "Q1_results.xlsx",
    sheet_name="Q1c_Covariance",
    header=3,
    index_col=0
)

# Extract Q1 parameters in the same asset order as Q2
m = params.loc[assets, "Annualised_Expected_Return"].to_numpy(dtype=float)
C = cov_df.loc[assets, assets].to_numpy(dtype=float)

# Extract Q2 baseline constraints
lower = np.array(
    config["recommended_constraints"]["lower_bounds"],
    dtype=float
)

upper = np.array(
    config["recommended_constraints"]["upper_bounds"],
    dtype=float
)

bounds = list(zip(lower, upper))

# Validate Q1 and Q2 consistency
assert len(assets) == 9
assert C.shape == (9, 9)
assert np.allclose(C, C.T)
assert np.allclose(m, config["mean"], atol=1e-10)
assert np.allclose(C, config["covariance"], atol=1e-10)
assert np.all(lower == 0)
assert np.all(upper == 0.5)
assert config["recommended_constraints"]["short_selling"] is False

print("Q1 parameters and Q2 baseline are consistent.")
print("Number of assets:", len(assets))
print("Individual asset weight bounds:", bounds[0])


# In[3]:


# Growth fractions for the nine indices
# Based on our previously selected Q3 classification

growth_by_index = {
    "ASA52 Index": 1.0,
    "NDDLWI Index": 1.0,
    "NDLEEGF Index": 1.0,
    "RDAU Index": 1.0,
    "FDCIISAH Index": 1.0,
    "HEDGNAV Index": 0.5,
    "BACM0 Index": 0.0,
    "H03432AU Index": 0.0,
    "BAUBIL Index": 0.0
}

# Check that all nine Q1 assets have been classified
assert set(assets) == set(growth_by_index)

# Match growth fractions to the Q2 asset order
g = np.array(
    [growth_by_index[asset] for asset in assets],
    dtype=float
)

# Defensive fraction = 1 - Growth fraction
d = 1 - g

# Display classification table
classification_table = pd.DataFrame({
    "Growth (%)": g * 100,
    "Defensive (%)": d * 100
}, index=assets)

classification_table.index.name = "Index"

display(classification_table)


# In[4]:


# Number of assets
n = len(assets)

# Minimum achievable Growth allocation
min_growth_result = linprog(
    c=g,
    A_eq=np.ones((1, n)),
    b_eq=[1.0],
    bounds=bounds,
    method="highs"
)

# Maximum achievable Growth allocation
max_growth_result = linprog(
    c=-g,
    A_eq=np.ones((1, n)),
    b_eq=[1.0],
    bounds=bounds,
    method="highs"
)

# Check optimisation success
assert min_growth_result.success
assert max_growth_result.success

# Feasible Growth allocation range
g_min = min_growth_result.fun
g_max = -max_growth_result.fun

print(f"Minimum feasible Growth allocation: {g_min:.2%}")
print(f"Maximum feasible Growth allocation: {g_max:.2%}")

# Q3(a) target allocations
growth_targets = {
    "Defensive": 0.30,
    "Balanced": 0.70,
    "Aggressive": 0.90
}

# Check each target
for name, target in growth_targets.items():
    feasible = (g_min - 1e-9 <= target <= g_max + 1e-9)

    print(
        f"{name} ({target:.0%} Growth / {1-target:.0%} Defensive): "
        f"{'Feasible' if feasible else 'Infeasible'}"
    )


# In[5]:


# Minimum Variance Portfolio Optimisation

def minimum_variance(target_growth):

    # Find a feasible starting portfolio
    feasible_result = linprog(
        c=np.zeros(n),
        A_eq=np.vstack([np.ones(n), g]),
        b_eq=np.array([1.0, target_growth]),
        bounds=bounds,
        method="highs"
    )

    if not feasible_result.success:
        raise ValueError(
            f"No feasible portfolio for Growth target {target_growth:.0%}"
        )

    # Portfolio constraints
    constraints = [
        {
            "type": "eq",
            "fun": lambda w: np.sum(w) - 1.0,
            "jac": lambda w: np.ones(n)
        },
        {
            "type": "eq",
            "fun": lambda w: g @ w - target_growth,
            "jac": lambda w: g
        }
    ]

    # Minimise annualised portfolio variance
    result = minimize(
        fun=lambda w: 100.0 * (w @ C @ w),
        x0=feasible_result.x,
        jac=lambda w: 200.0 * (C @ w),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={
            "ftol": 1e-12,
            "maxiter": 10000
        }
    )

    if not result.success:
        raise RuntimeError(
            f"Optimisation failed: {result.message}"
        )

    w = result.x

    # Validate portfolio constraints
    assert np.isclose(np.sum(w), 1.0, atol=1e-7)
    assert np.isclose(g @ w, target_growth, atol=1e-7)
    assert np.all(w >= lower - 1e-7)
    assert np.all(w <= upper + 1e-7)

    return w


# Optimise the three Q3(a) portfolios
portfolios = {
    name: minimum_variance(target)
    for name, target in growth_targets.items()
}

# Portfolio weights table
weights_table = pd.DataFrame(
    portfolios,
    index=assets
)

weights_table.index.name = "Index"

print("Minimum Variance Portfolio Weights (%)")
display((weights_table * 100).round(4))

# Verify total weights and Growth allocations
print("\nPortfolio Constraint Checks")

for name, w in portfolios.items():
    print(
        f"{name}: "
        f"Total Weight = {np.sum(w):.2%}, "
        f"Growth = {g @ w:.2%}, "
        f"Maximum Asset Weight = {np.max(w):.2%}"
    )


# In[6]:


# Cell 6 — Portfolio Performance Comparison

# Risk-free rate proxy:
# Annualised historical mean return of BAUBIL Index from Q1
rf = float(
    params.loc["BAUBIL Index", "Annualised_Expected_Return"]
)

# Calculate portfolio performance
results = []

for name, w in portfolios.items():

    # Expected annualised portfolio return
    expected_return = float(w @ m)

    # Annualised portfolio volatility
    volatility = float(np.sqrt(w @ C @ w))

    # Sharpe ratio
    sharpe_ratio = (expected_return - rf) / volatility

    # Growth and Defensive allocations
    growth_allocation = float(g @ w)
    defensive_allocation = float(d @ w)

    results.append({
        "Portfolio": name,
        "Growth (%)": growth_allocation * 100,
        "Defensive (%)": defensive_allocation * 100,
        "Expected Return (%)": expected_return * 100,
        "Volatility (%)": volatility * 100,
        "Sharpe Ratio": sharpe_ratio
    })

# Create comparison table
results_table = pd.DataFrame(results).set_index("Portfolio")

print(f"Risk-free rate proxy: {rf:.4%}")
print("\nQ3(a) — Minimum Variance Portfolio Performance Comparison")

display(results_table.round(4))

