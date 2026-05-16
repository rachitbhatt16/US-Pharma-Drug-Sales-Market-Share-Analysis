# 💊 US Pharma Drug Sales & Market Share Analysis


## 📌 Business Problem

A pharma client wants to understand:
- Which **drug categories** are growing fastest?
- Which **manufacturers** are gaining or losing market share?
- Where is **pricing pressure** highest — and what are the regulatory implications?
- Where should **sales force investment** be focused?

This project replicates the kind of analytical deliverable a pharma strategy consulting firm (e.g. Blue Matter) would produce for a biotech or pharmaceutical client.

---

## 🗂️ Dataset

| Detail | Info |
|---|---|
| Source | [FDA Medicare Drug Spending — Kaggle](https://www.kaggle.com/datasets/iqmanuel/medicare-drug-spending) |
| Records | 100,000+ rows |
| Brands | 1,200+ unique drugs |
| Period | 2011 – 2020 |
| Coverage | US Medicare market |

---

## 🛠️ Tools & Tech Stack

| Layer | Tools Used |
|---|---|
| Data Cleaning & EDA | Python (Pandas, NumPy, Seaborn, Matplotlib) |
| Data Storage & Querying | SQL (SQLite) |
| Dashboard | Power BI (DAX measures) |
| Presentation | PowerPoint (3-slide client deck) |

---

## 🔍 What This Project Does

### Step 1 — Data Loading & Inspection
- Loads FDA Medicare drug spending CSV
- Inspects shape, data types, missing values

### Step 2 — Data Cleaning
- Standardises column names
- Cleans currency fields, handles nulls
- Assigns therapeutic categories (Oncology, Cardiovascular, Diabetes, Immunology, Neurology, Respiratory, Rare Disease, Infectious Disease) based on drug name mapping

### Step 3 — SQL Analysis (6 Queries)
| Query | Business Question |
|---|---|
| Q1 | Total US pharma spend by year |
| Q2 | Top 10 drugs by total revenue |
| Q3 | Market share by manufacturer |
| Q4 | Spend by therapeutic category |
| Q5 | Drug price inflation (unit cost % increase) |
| Q6 | Manufacturer YoY spend growth (LAG window function) |

### Step 4 — Visual Dashboard (6 Charts)
- Total market spend trend by year
- Top 10 drugs by cumulative revenue
- Manufacturer market share (pie)
- Therapeutic category benchmarking
- Drug price inflation ranking
- YoY manufacturer growth comparison

### Step 5 — Executive Summary
- Auto-generates key findings and a ready-to-use resume bullet based on actual dataset numbers

---

## 📊 Key Findings

- **Oncology and Immunology** are the highest-spend and fastest-growing therapeutic categories — indicating strong market opportunity and intensifying competitive pressure
- **Top 5 manufacturers** control the majority of total US pharma market spend — high concentration risk with M&A implications
- **Specialty drug unit costs** increased significantly post-2015 — regulatory and pricing strategy implications for pharma clients
- **YoY growth varies sharply** by manufacturer — signals pipeline wins, patent cliffs, and biosimilar entry effects

---

## 📁 Repository Structure

```
us-pharma-drug-spending-analysis/
│
├── fda_drug_spending_analysis.py   # Full Python + SQL analysis script
├── pharma_dashboard.png            # 6-chart visual output (generated on run)
├── pharma_analysis.db              # SQLite database (generated on run)
└── README.md                       # Project overview
```

---

## ▶️ How to Run

```bash
# 1. Install dependencies
pip install pandas matplotlib seaborn

# 2. Download dataset from Kaggle
# https://www.kaggle.com/datasets/iqmanuel/medicare-drug-spending
# Rename file to: fda_drug_spending.csv
# Place in same folder as the script

# 3. Run the script
python fda_drug_spending_analysis.py
```

**Output files generated:**
- `pharma_dashboard.png` — 6-chart analytical dashboard
- `pharma_analysis.db` — SQLite database with all query results

---

## 📈 Sample Output

> *"Analysed $48Bn+ in US pharmaceutical drug spending across 1,200+ brands (2011–2020) using Python & SQL — identified Oncology as highest-spend therapeutic area and surfaced manufacturer market share concentration risk, framed as a pharma consulting client deliverable"*

---

## 👤 Author

**Rachit Bhatt**
MBA — Finance & Business Analytics | Delhi Technological University
[LinkedIn](https://www.linkedin.com/in/rachitbhatt16) · [GitHub](https://github.com/rachitbhatt16)

---

## 📄 License

This project uses publicly available data from the FDA via Kaggle. For educational and portfolio purposes only.
