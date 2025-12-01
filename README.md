# IESE Business Case – Monte Carlo Decision Model

This repository contains the code and data used to build a Monte Carlo–based decision model for **IESE Business School’s Case 1** (RELE Rouen).  

The model compares three strategic options:

- **RELE** – Continue with the current franchise and positioning  
- **OILTS** – Switch to the OILTS franchise, with renovation and a different business model  
- **SELL** – Accept an external offer and exit the business

The engine combines:
- Historical financial and operational data  
- Economic calibration (prices, cost ratios, debt schedule)  
- A Monte Carlo simulation of future demand  
- Intangible factors (moral, reputation, academic project) converted into a monetary **NEV (Net Equity Value)**

---

## 1. Repository structure

```text
.
├── data/
│   ├── income_statement_2017_2022.csv      # Historical P&L and key costs (input)
│   ├── student_weeks_history.csv           # Historical demand in student-weeks (input)
│   └── scenario_summary.csv                # Monte Carlo scenario results (generated output)
│
├── model/
│   ├── engine.py                           # Core economic engine + Monte Carlo logic
│   ├── scenarios.py                        # Global parameters, strategies, scenario definitions
│   └── __init__.py                         # Makes "model" a Python package
│
├── notebooks/
│   ├── 01_data_exploration.ipynb           # Basic exploration of historical data
│   ├── 02_model_engine.ipynb               # How to call and test the model engine
│   └── 03_montecarlo_simulations.ipynb     # Full scenario analysis and CSV export
│
├── environment.yml                         # Conda environment specification
├── .gitignore                              # Files and folders ignored by git
└── README.md                               # This file
