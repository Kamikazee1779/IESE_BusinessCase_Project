import copy

# ===============================
# 0) Global parameters (base)
# ===============================

globalParams = {
    "T": 3,                  # projection horizon in years
    "N_Sim": 1000000,        # number of Monte Carlo simulations
    "K": 0.08,               # discount rate
    "alpha_M": 150000,       # € equivalent for Moral (0->10)
    "alpha_R": 75000,        # € equivalent for Reputation (0->10)
    "alpha_A": 100000,       # € equivalent for Academic project (0->10)
    "Debt_Payment": 50000,   # annual debt service
    "Debt_Years": 5,         # years with debt
    "OILTS_renovation_cost": 200000.0,  # one-off renovation cost for OILTS
}

strategies = ["RELE", "OILTS", "SELL"]

# ===============================
# 0.1) Strategy parameters (base)
# ===============================

params = {
    "RELE": {
        # --- Core economics (case base 2022) ---
        "royalty_rate": 0.16,       # ~15–16% effective in the case
        "price_week": 2500.0,       # €/student-week, standard
        "price_weekend": 2500.0,    # €/weekend student (RELE weekend program)

        # --- Intangibles (0–10) ---
        "admin_score": 8.5,         # strong care for staff, family feel
        "prestige_score": 7.0,
        "reputation_score": 7.5,    # good reputation, but smaller network than OILTS
        "brand_base_score": 7.5,    # strong academic project

        # Internal weights for intangible graph
        "w_admin_moral": 0.6,
        "beta_prestige_rep": 0.4,
        "beta_brand_rep": 0.5,

        # Demand multipliers (will be overwritten after CSV calibration)
        "demand_mult_std": 1.0,
        "demand_mult_wkd": 1.0,
    },

    "OILTS": {
        # --- Core economics (case base) ---
        # 1000€ tuition ≈ 1450€ total (tuition + lodging) per week
        "royalty_rate": 0.035,      # ~5% on tuition ≈ 3.5% on total revenue
        "price_week": 1450.0,       # €/student-week (total: tuition + lodging)
        "price_weekend": 400.0,     # 2 days ≈ 400€ tuition-equivalent (for future scenarios)

        "fixed_cost_base": 0.0,
        "var_cost_per_student_week": 0.0,
        "var_cost_per_student_weekend": 0.0,

        # Intangibles: more “brand” and external reputation, less “family”
        "admin_score": 7.0,
        "prestige_score": 7.0,
        "reputation_score": 8.5,    # strong global franchise reputation
        "brand_base_score": 7.5,

        "w_admin_moral": 0.6,
        "beta_prestige_rep": 0.4,
        "beta_brand_rep": 0.5,

        # Demand multipliers (will be overwritten after CSV calibration)
        "demand_mult_std": 1.0,
        "demand_mult_wkd": 0.0,     # base case: no weekend program yet in Rouen
    },

    "SELL": {
        # Offer from EFEL ≈ 2.1M€ for business + house
        "house_expected_value": 2_100_000.0,

        # Intangibles if they sell: low
        "admin_score": 3.0,
        "prestige_score": 2.0,
        "reputation_score": 1.0,
        "brand_base_score": 0.0,

        "w_admin_moral": 0.6,
        "beta_prestige_rep": 0.4,
        "beta_brand_rep": 0.5,
    }
}

# ===============================
# Scenario grid definition
# (10 key scenarios, OILTS 5% base royalty)
# ===============================

scenario_defs = [
    # 1. Base case – everything as in base parameters
    {
        "name": "Base case",
        "global": {},
        "RELE": {},
        "OILTS": {},
        "SELL": {},
    },

    # 2. Mild demand downside (both RELE and OILTS)
    {
        "name": "Mild demand downside",
        "global": {},
        "RELE": {
            "demand_mult_std": 0.90,
            "demand_mult_wkd": 0.90,
        },
        "OILTS": {
            "demand_mult_std": 0.90,
            "demand_mult_wkd": 0.90,
        },
        "SELL": {},
    },

    # 3. Mild demand upside (both RELE and OILTS)
    {
        "name": "Mild demand upside",
        "global": {},
        "RELE": {
            "demand_mult_std": 1.10,
            "demand_mult_wkd": 1.10,
        },
        "OILTS": {
            "demand_mult_std": 1.10,
            "demand_mult_wkd": 1.10,
        },
        "SELL": {},
    },

    # 4. Cost inflation shock (higher operating costs for everyone)
    {
        "name": "Cost inflation shock",
        "global": {
            # +6 percentage points on other operating rate (e.g. 0.66 -> 0.72)
            "other_operating_rate_base_shift": +0.06,
        },
        "RELE": {},
        "OILTS": {},
        "SELL": {},
    },

    # 5. Lean staffing, low morale (cost savings vs intangibles)
    {
        "name": "Lean staffing, low morale",
        "global": {
            # -4 percentage points on other operating rate (cost savings)
            "other_operating_rate_base_shift": -0.04,
        },
        "RELE": {
            # less staff / more pressure -> lower morale
            "admin_score": 6.0,  # from 8.5
        },
        "OILTS": {
            "admin_score": 5.0,  # from 7.0
        },
        "SELL": {},
    },

    # 6. RELE quality focus (invest more in project quality and reputation)
    {
        "name": "RELE quality focus",
        "global": {
            # small increase in operating costs due to quality investments
            "other_operating_rate_base_shift": +0.02,
        },
        "RELE": {
            "reputation_score": 8.5,    # from 7.5
            "brand_base_score": 8.0,    # from 7.5
        },
        "OILTS": {},
        "SELL": {},
    },

    # 7. OILTS better franchise deal (rare improved contract: royalty 4%)
    {
        "name": "OILTS better franchise deal",
        "global": {},
        "RELE": {},
        "OILTS": {
            "royalty_rate": 0.04,       # better than the standard 5%
            "reputation_score": 9.0,    # slightly stronger perceived franchise quality
        },
        "SELL": {},
    },

    # 8. OILTS worse franchise deal (rare worse contract: royalty 6%)
    {
        "name": "OILTS worse franchise deal",
        "global": {},
        "RELE": {},
        "OILTS": {
            "royalty_rate": 0.06,       # worse than the standard 5%
            # reputation_score unchanged here
        },
        "SELL": {},
    },

    # 9. Aggressive OILTS growth (higher demand, higher complexity)
    {
        "name": "Aggressive OILTS growth",
        "global": {
            # slightly higher operating costs due to growth complexity
            "other_operating_rate_base_shift": +0.03,
        },
        "RELE": {},
        "OILTS": {
            "demand_mult_std": 1.15,
            "demand_mult_wkd": 1.15,
            "reputation_score": 9.0,    # stronger perceived brand
            "brand_base_score": 7.5,    # slightly higher academic profile
        },
        "SELL": {},
    },

    # 10. Attractive exit market (house value significantly higher)
    {
        "name": "Attractive exit market",
        "global": {},
        "RELE": {},
        "OILTS": {},
        "SELL": {
            # e.g. +20% vs base house value 1.2M -> 1.44M
            "house_expected_value": 1_440_000.0,
        },
    },
]

# ===============================
# Scenario application helper
# ===============================

def apply_scenario(base_globalParams, base_params, scenario_def):
    """
    Returns (scenario_globalParams, scenario_params) as deep copies of the base,
    with scenario-specific overrides applied.
    """
    gp = copy.deepcopy(base_globalParams)
    ps = copy.deepcopy(base_params)

    # 1) Global updates
    gupd = scenario_def.get("global", {})
    for key, value in gupd.items():
        if key == "other_operating_rate_base_shift":
            # shift relative to calibrated base
            gp["other_operating_rate_base"] = (
                base_globalParams["other_operating_rate_base"] + value
            )
        else:
            gp[key] = value

    # 2) Per-strategy updates
    for strat in ["RELE", "OILTS", "SELL"]:
        if strat in scenario_def:
            upd = scenario_def[strat]
            for key, value in upd.items():
                ps[strat][key] = value

    return gp, ps

