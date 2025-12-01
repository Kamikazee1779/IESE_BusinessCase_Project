# IESE Business Case – Monte Carlo Decision Model

This repository contains the complete implementation of a **quantitative Monte Carlo model** designed to evaluate strategic decisions for a real business case studied at **IESE Business School**.

The project includes:

- Economic calibration from historical financials  
- Demand uncertainty modeling  
- Multi-strategy comparison (RELE, OILTS, SELL)  
- Intangible valuation (Moral, Reputation, Academic Project)  
- Scenario analysis across 10 predefined cases  
- Multi-horizon projections (2, 5, 7, 10 years)  
- Fully reproducible environment  

---

# 1. Requirements

To run this project **exactly as intended**, the following are required:

### ✔ **Anaconda / Miniconda (mandatory)**  
This project uses a Conda environment defined in `environment.yml`.  
Installing via pip is NOT supported due to dependency management.

Download here:  
https://www.anaconda.com/download

### ✔ Git (optional but recommended)  
If not available, you may download the ZIP instead.

---

# 2. Repository Structure

IESE_BusinessCase_Project/
│
├── data/ ← Input data (visible)
│ ├── income_statement_2017_2022.csv
│ └── student_weeks_history.csv
│
├── notebooks/
│ ├── 01_data_exploration.ipynb
│ ├── 02_model_engine.ipynb
│ └── 03_montecarlo_simulations.ipynb
│
├── model/
│ └── business_logic.py
│
├── environment.yml
├── README.md
└── .gitignore

---

# 3. How to Run This Project

## A) Using Git (recommended)

1. Clone the repository:
git clone https://github.com/Kamikazee1779/IESE_BusinessCase_Project.git
cd IESE_BusinessCase_Project

2. Create the Conda environment:
conda env create -f environment.yml

3. Activate the environment: 
conda activate business_case_iese

4. Launch Jupyter Notebook:
jupyter notebook

5. Open: 
notebooks/03_montecarlo_simulations.ipynb

And run all cells to generate scenario_summary.csv

## B) Using ZIP download

1. Download ZIP
2. Extract
3. Open terminal inside the folder
4. Run steps 2–5 above

---

# 4. Output

Running the full simulation produces the file: scenario_summary.csv

which contains:

- Expected NEV (economic + intangibles)
- VaR 5% (downside risk)
- CVaR 5% (tail risk)
- Probability that RELE or OILTS outperform SELL
- Results across all 10 scenarios × 4 projection horizons
- The output allows for a full comparative analysis of strategic options under uncertainty.

---

# 5. Notes 
- All required data to run the project is included in the data/ folder.
- The environment.yml guarantees full reproducibility.
- The core simulation logic is inside 03_montecarlo_simulations.ipynb.
- No confidential or sensitive information is used.