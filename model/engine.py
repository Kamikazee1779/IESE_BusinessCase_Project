import numpy as np
import matplotlib.pyplot as plt


# ===============================
# 4. Business engine + Monte Carlo
# ===============================

def sample_demand(strategy: str, globalParams: dict, params: dict, rng=None):
    """
    Generate demand paths (standard student-weeks and weekend students)
    for a given strategy.
    """
    if rng is None:
        rng = np.random.default_rng()

    T = globalParams["T"]
    N = globalParams["N_Sim"]

    mean_std = globalParams["stud_std_mean"]
    std_std  = globalParams["stud_std_std"]
    mean_wkd = globalParams["stud_wkd_mean"]
    std_wkd  = globalParams["stud_wkd_std"]

    cfg = params[strategy]
    mult_std = cfg.get("demand_mult_std", 1.0)
    mult_wkd = cfg.get("demand_mult_wkd", 1.0)

    mu_std = mean_std * mult_std
    mu_wkd = mean_wkd * mult_wkd

    students_std = rng.normal(loc=mu_std, scale=std_std, size=(N, T))
    students_wkd = rng.normal(loc=mu_wkd, scale=std_wkd, size=(N, T))

    students_std = np.clip(students_std, 0, None)
    students_wkd = np.clip(students_wkd, 0, None)

    return students_std, students_wkd


def build_debt_schedule(globalParams: dict) -> np.ndarray:
    """
    Returns an array (T,) with the annual debt service.
    """
    T = globalParams["T"]
    debt = np.zeros(T, dtype=float)
    years = min(T, globalParams["Debt_Years"])
    debt[:years] = globalParams["Debt_Payment"]
    return debt


def compute_revenue(students_std, students_wkd, strategy: str,
                    globalParams: dict, params: dict):
    """
    Revenues = price_std * student-weeks + price_wkd * weekend students.
    """
    cfg = params[strategy]
    price_std = cfg.get("price_week",    globalParams["price_std_base"])
    price_wkd = cfg.get("price_weekend", globalParams["price_wkd_base"])

    students_std = np.asarray(students_std, dtype=float)
    students_wkd = np.asarray(students_wkd, dtype=float)

    revenue = price_std * students_std + price_wkd * students_wkd
    return revenue


def compute_operating_costs(revenue, strategy: str,
                            globalParams: dict, params: dict):
    """
    Operating cash costs = (royalty_rate + other_op_rate) * revenue.
    """
    cfg = params[strategy]
    royalty_rate = cfg.get("royalty_rate", globalParams["royalty_rate_base"])
    other_op_rate = globalParams["other_operating_rate_base"]
    revenue = np.asarray(revenue, dtype=float)
    op_cost = (royalty_rate + other_op_rate) * revenue
    return op_cost


def compute_cashflows_for_strategy(students_std, students_wkd, strategy: str,
                                   globalParams: dict, params: dict):
    """
    Returns cashflows (N_sim, T) for RELE or OILTS.
    For SELL it is not used (handled separately).

    Note: if strategy is OILTS, we apply a one-off renovation cost
    in the first year (t = 1).
    """
    T = globalParams["T"]
    revenue = compute_revenue(students_std, students_wkd, strategy, globalParams, params)
    op_cost = compute_operating_costs(revenue, strategy, globalParams, params)
    debt_sched = build_debt_schedule(globalParams)  # (T,)

    total_cost = op_cost + debt_sched  # broadcasting
    cf = revenue - total_cost

    # Additional renovation cost ONLY for OILTS
    if strategy == "OILTS":
        renovation = globalParams.get("OILTS_renovation_cost", 0.0)
        cf[..., 0] -= renovation  # apply in year 1

    return cf


def discount_cashflows(cashflows, globalParams: dict):
    """
    Discount cashflows and return NPV.
    cashflows:
      - shape (T,)     -> scalar
      - shape (N_sim,T)-> array (N_sim,)
    """
    cf = np.asarray(cashflows, dtype=float)
    k = globalParams["K"]

    if cf.ndim == 1:
        T = cf.shape[0]
        factors = 1.0 / (1.0 + k) ** np.arange(1, T + 1)
        return float((cf * factors).sum())
    elif cf.ndim == 2:
        N_sim, T = cf.shape
        factors = 1.0 / (1.0 + k) ** np.arange(1, T + 1)
        return (cf * factors).sum(axis=1)
    else:
        raise ValueError("cashflows must be 1D or 2D")


def npv_for_strategy(strategy: str, globalParams: dict, params: dict, rng=None):
    """
    - For RELE and OILTS: simulates demand, computes CF and returns NPV (array N_sim,).
    - For SELL: returns a constant NPV economic array.
    """
    if rng is None:
        rng = np.random.default_rng()

    N = globalParams["N_Sim"]

    if strategy == "SELL":
        house_val = params["SELL"]["house_expected_value"]
        total_debt = globalParams["Debt_Payment"] * globalParams["Debt_Years"]
        npv_econ_sell = house_val - total_debt
        return np.full(N, npv_econ_sell, dtype=float)

    # Operating strategies: RELE / OILTS
    students_std, students_wkd = sample_demand(strategy, globalParams, params, rng)
    cf = compute_cashflows_for_strategy(students_std, students_wkd, strategy, globalParams, params)
    npv_econ = discount_cashflows(cf, globalParams)
    return npv_econ


# ===============================
# 5. Intangibles and NEV
# ===============================

def get_intangible_scores(strategy: str, params: dict):
    """
    Returns intangible scores (0–10) for:
      - Moral (M)
      - Reputation (R)
      - Academic / Brand (A)
    """
    cfg = params[strategy]
    admin   = cfg["admin_score"]
    rep     = cfg["reputation_score"]
    brand_b = cfg["brand_base_score"]
    prest_b = cfg["prestige_score"]

    w_admin_moral  = cfg.get("w_admin_moral", 0.6)
    beta_prest_rep = cfg.get("beta_prestige_rep", 0.4)
    beta_brand_rep = cfg.get("beta_brand_rep", 0.5)

    prestige = np.clip(prest_b + beta_prest_rep * rep, 0.0, 10.0)
    moral    = np.clip(w_admin_moral * admin + (1.0 - w_admin_moral) * prestige, 0.0, 10.0)
    academic = np.clip(brand_b + beta_brand_rep * rep, 0.0, 10.0)

    return {"M": float(moral), "R": float(rep), "A": float(academic)}


def intangible_values_eur(strategy: str, params: dict, globalParams: dict):
    """
    Converts intangible scores into € amounts using:
      alpha_M, alpha_R, alpha_A.
    """
    scores = get_intangible_scores(strategy, params)
    M, R, A = scores["M"], scores["R"], scores["A"]

    M_n, R_n, A_n = M / 10.0, R / 10.0, A / 10.0

    alpha_M = globalParams["alpha_M"]
    alpha_R = globalParams["alpha_R"]
    alpha_A = globalParams["alpha_A"]

    V_M = alpha_M * M_n
    V_R = alpha_R * R_n
    V_A = alpha_A * A_n

    return {
        "M": M, "R": R, "A": A,
        "M_n": M_n, "R_n": R_n, "A_n": A_n,
        "V_M": V_M, "V_R": V_R, "V_A": V_A,
    }


def compute_nev(npv_econ, strategy: str, params: dict, globalParams: dict):
    """
    NEV = economic NPV + intangible € values (M + R + A).
    """
    npv_econ = np.asarray(npv_econ, dtype=float)
    iv = intangible_values_eur(strategy, params, globalParams)
    NEV = npv_econ + iv["V_M"] + iv["V_R"] + iv["V_A"]
    return NEV


def analyze_status_quo(globalParams: dict, params: dict, strategy: str = "RELE",
                       plot: bool = True):
    """
    Analyze the deterministic 'status quo' of a given strategy (default RELE),
    using historical mean demand as a constant path.
    """
    T = globalParams["T"]
    years = np.arange(1, T + 1)

    # Constant demand = historical means
    mean_std = globalParams["stud_std_mean"]
    mean_wkd = globalParams["stud_wkd_mean"]

    students_std = np.full((1, T), mean_std, dtype=float)
    students_wkd = np.full((1, T), mean_wkd, dtype=float)

    # Economic engine
    revenue = compute_revenue(students_std, students_wkd,
                              strategy, globalParams, params)   # (1, T)
    op_cost = compute_operating_costs(revenue, strategy, globalParams, params)  # (1, T)
    debt_sched = build_debt_schedule(globalParams)                              # (T,)

    total_cost = op_cost + debt_sched  # (1, T)
    cf = revenue - total_cost          # (1, T)

    # Deterministic economic NPV
    npv_econ = discount_cashflows(cf, globalParams)[0]
    # Deterministic NEV (adding intangibles)
    nev = compute_nev(npv_econ, strategy, params, globalParams)

    print(f"=== Deterministic status quo for {strategy} ===")
    print(f"Average standard demand : {mean_std:.1f} student-weeks/year")
    print(f"Average weekend demand  : {mean_wkd:.1f} students/year")
    print(f"Deterministic economic NPV : {npv_econ:,.0f} €")
    print(f"Deterministic total NEV    : {nev:,.0f} €")

    if plot:
        rev = revenue[0]
        tot_cost = total_cost[0]
        cf_line = cf[0]

        plt.figure()
        plt.plot(years, rev, marker="o", label="Revenues")
        plt.plot(years, tot_cost, marker="o", label="Total costs (operating + debt)")
        plt.plot(years, cf_line, marker="o", label="Cashflow")
        plt.axhline(0, color="black", linewidth=0.8)
        plt.title(f"Deterministic status quo – strategy {strategy}")
        plt.xlabel("Year")
        plt.ylabel("€")
        plt.legend()
        plt.tight_layout()
        plt.show()

    return {
        "npv_econ": npv_econ,
        "nev": float(nev),
        "revenue": revenue[0],
        "total_cost": total_cost[0],
        "cashflow": cf[0],
    }


# ===============================
# 6. Simulation per strategy
# ===============================

def simulate_strategy(strategy: str, globalParams: dict, params: dict, rng=None):
    """
    Returns:
      - npv_econ: array (N_sim,)
      - nev: array (N_sim,)
    """
    if rng is None:
        rng = np.random.default_rng()
    npv_econ = npv_for_strategy(strategy, globalParams, params, rng)
    nev = compute_nev(npv_econ, strategy, params, globalParams)
    return {"npv_econ": npv_econ, "nev": nev}


def run_all_strategies(globalParams: dict, params: dict, strategies: list):
    """
    Runs the Monte Carlo for each strategy and returns:
      - results: dict with full distributions
      - summary: list of dicts with EU, VaR5, CVaR5, P(NEV > SELL)
    """
    rng = np.random.default_rng(123)
    results = {}
    for s in strategies:
        results[s] = simulate_strategy(s, globalParams, params, rng)

    # Summary per strategy
    summary = []
    sell_nev = results["SELL"]["nev"]
    for s in strategies:
        NEV = results[s]["nev"]
        EU = NEV.mean()
        VaR5 = np.percentile(NEV, 5)
        CVaR5 = NEV[NEV <= VaR5].mean()
        if s == "SELL":
            P_better_than_sell = np.nan
        else:
            P_better_than_sell = (NEV > sell_nev).mean()
        summary.append({
            "strategy": s,
            "EU": EU,
            "VaR5": VaR5,
            "CVaR5": CVaR5,
            "P(NEV > SELL)": P_better_than_sell,
        })

    return results, summary

