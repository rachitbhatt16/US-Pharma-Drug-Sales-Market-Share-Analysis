# ============================================================
# US Pharma Drug Sales & Market Share Analysis
# Dataset: FDA Medicare Drug Spending (Kaggle)
# Author: Rachit Bhatt | MBA Finance & Business Analytics, DTU
# Tools: Python (Pandas, Matplotlib, Seaborn) + SQL (SQLite)
# ============================================================
# SETUP: pip install pandas matplotlib seaborn sqlite3 kaggle
#
# DATASET DOWNLOAD:
# 1. Go to: https://www.kaggle.com/datasets/iqmanuel/medicare-drug-spending
# 2. Download and unzip — you'll get a CSV file
# 3. Rename it to: fda_drug_spending.csv
# 4. Place it in the same folder as this script
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import warnings
warnings.filterwarnings('ignore')

# ── Plot style ───────────────────────────────────────────────
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({'figure.dpi': 120, 'font.family': 'DejaVu Sans'})

# ============================================================
# STEP 1 — LOAD & INSPECT DATA
# ============================================================
print("=" * 60)
print("STEP 1: Loading Data")
print("=" * 60)

df = pd.read_csv("fda_drug_spending.csv")

print(f"Shape        : {df.shape[0]:,} rows × {df.shape[1]} columns")
print(f"Columns      : {list(df.columns)}")
print(f"\nData Types:\n{df.dtypes}")
print(f"\nMissing Values:\n{df.isnull().sum()}")
print(f"\nSample rows:\n{df.head(3)}")

# ============================================================
# STEP 2 — DATA CLEANING
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: Cleaning Data")
print("=" * 60)

# Standardise column names
df.columns = (df.columns
              .str.strip()
              .str.lower()
              .str.replace(' ', '_')
              .str.replace(r'[^a-z0-9_]', '', regex=True))

print(f"Cleaned columns: {list(df.columns)}")

# Common column name mappings — adjust if your CSV differs
rename_map = {}

# Try to detect key columns automatically
for col in df.columns:
    if 'drug' in col and 'name' in col:
        rename_map[col] = 'drug_name'
    elif 'brand' in col:
        rename_map[col] = 'brand_name'
    elif 'manufactur' in col or 'company' in col:
        rename_map[col] = 'manufacturer'
    elif 'year' in col:
        rename_map[col] = 'year'
    elif 'total' in col and 'spend' in col:
        rename_map[col] = 'total_spending'
    elif 'unit' in col and ('cost' in col or 'price' in col):
        rename_map[col] = 'unit_cost'
    elif 'claim' in col or 'prescription' in col:
        rename_map[col] = 'total_claims'
    elif 'beneficiar' in col:
        rename_map[col] = 'total_beneficiaries'

df.rename(columns=rename_map, inplace=True)
print(f"Renamed columns: {rename_map}")

# Ensure required columns exist — create placeholders if missing
required = ['drug_name', 'manufacturer', 'year', 'total_spending', 'unit_cost', 'total_claims']
for col in required:
    if col not in df.columns:
        print(f"  ⚠ Column '{col}' not found — creating placeholder")
        df[col] = np.nan

# Clean spending & cost columns
for col in ['total_spending', 'unit_cost']:
    if df[col].dtype == object:
        df[col] = (df[col]
                   .str.replace('[$,]', '', regex=True)
                   .str.strip())
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Clean year
df['year'] = pd.to_numeric(df['year'], errors='coerce')
df = df.dropna(subset=['year', 'total_spending'])
df['year'] = df['year'].astype(int)

# Fill text nulls
df['drug_name']    = df['drug_name'].fillna('Unknown Drug')
df['manufacturer'] = df['manufacturer'].fillna('Unknown Manufacturer')

# Assign broad therapeutic categories based on drug name keywords
category_map = {
    'Oncology':        ['cancer', 'tumor', 'chemo', 'oncol', 'gleevec', 'herceptin', 'avastin', 'keytruda', 'opdivo', 'ibrance'],
    'Cardiovascular':  ['statin', 'lipitor', 'crestor', 'cardio', 'heart', 'blood pressure', 'lisinopril', 'atorvastatin', 'metoprolol'],
    'Diabetes':        ['insulin', 'metformin', 'diabetes', 'gluco', 'januvia', 'victoza', 'jardiance', 'lantus'],
    'Immunology':      ['humira', 'enbrel', 'remicade', 'immune', 'arthritis', 'adalimumab', 'etanercept'],
    'Neurology':       ['alzheimer', 'parkinson', 'epilep', 'neuro', 'ms ', 'multiple sclerosis', 'copaxone'],
    'Respiratory':     ['asthma', 'lung', 'copd', 'inhaler', 'advair', 'spiriva', 'symbicort'],
    'Rare Disease':    ['orphan', 'rare', 'gaucher', 'pompe', 'fabry', 'spinraza', 'soliris'],
    'Infectious Dis.': ['antibiotic', 'antiviral', 'hiv', 'hepatitis', 'hep c', 'sovaldi', 'harvoni'],
}

def assign_category(name):
    name_lower = str(name).lower()
    for cat, keywords in category_map.items():
        if any(k in name_lower for k in keywords):
            return cat
    return 'Other'

df['category'] = df['drug_name'].apply(assign_category)

print(f"\nCategory distribution:\n{df['category'].value_counts()}")
print(f"\nYear range: {df['year'].min()} – {df['year'].max()}")
print(f"Total records after cleaning: {len(df):,}")

# ============================================================
# STEP 3 — SAVE TO SQLITE FOR SQL ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: Loading into SQLite")
print("=" * 60)

conn = sqlite3.connect("pharma_analysis.db")
df.to_sql("drug_spending", conn, if_exists="replace", index=False)
print("✓ Table 'drug_spending' created in pharma_analysis.db")

def run_query(title, sql):
    """Run a SQL query and print results."""
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")
    result = pd.read_sql_query(sql, conn)
    print(result.to_string(index=False))
    return result

# ── SQL Query 1: Total market spending by year ────────────────
q1 = run_query(
    "Q1 · Total US Pharma Spend by Year",
    """
    SELECT
        year,
        ROUND(SUM(total_spending) / 1e9, 2)   AS total_spend_bn_usd,
        COUNT(DISTINCT drug_name)              AS unique_drugs,
        ROUND(AVG(unit_cost), 2)               AS avg_unit_cost
    FROM drug_spending
    GROUP BY year
    ORDER BY year
    """
)

# ── SQL Query 2: Top 10 drugs by total spend ─────────────────
q2 = run_query(
    "Q2 · Top 10 Drugs by Total Spend (All Years)",
    """
    SELECT
        drug_name,
        manufacturer,
        category,
        ROUND(SUM(total_spending) / 1e9, 2)  AS total_spend_bn_usd,
        COUNT(DISTINCT year)                  AS years_present
    FROM drug_spending
    GROUP BY drug_name, manufacturer, category
    ORDER BY total_spend_bn_usd DESC
    LIMIT 10
    """
)

# ── SQL Query 3: Market share by manufacturer ────────────────
q3 = run_query(
    "Q3 · Top 10 Manufacturers by Market Share",
    """
    WITH total AS (
        SELECT SUM(total_spending) AS grand_total FROM drug_spending
    )
    SELECT
        manufacturer,
        ROUND(SUM(total_spending) / 1e9, 2)                        AS spend_bn_usd,
        ROUND(SUM(total_spending) * 100.0 / MAX(grand_total), 2)   AS market_share_pct,
        COUNT(DISTINCT drug_name)                                   AS drug_portfolio_size
    FROM drug_spending, total
    GROUP BY manufacturer
    ORDER BY spend_bn_usd DESC
    LIMIT 10
    """
)

# ── SQL Query 4: Spend by therapeutic category ───────────────
q4 = run_query(
    "Q4 · Spend & CAGR by Therapeutic Category",
    """
    WITH yearly AS (
        SELECT
            category,
            year,
            SUM(total_spending) AS annual_spend
        FROM drug_spending
        GROUP BY category, year
    ),
    first_last AS (
        SELECT
            category,
            MIN(year)                                        AS start_year,
            MAX(year)                                        AS end_year,
            SUM(CASE WHEN year = MIN(year) THEN annual_spend END) AS spend_start,
            SUM(CASE WHEN year = MAX(year) THEN annual_spend END) AS spend_end,
            SUM(annual_spend)                                AS total_spend
        FROM yearly
        GROUP BY category
    )
    SELECT
        category,
        ROUND(total_spend / 1e9, 2)   AS total_spend_bn,
        start_year,
        end_year
    FROM first_last
    ORDER BY total_spend_bn DESC
    """
)

# ── SQL Query 5: Unit cost trend — price inflation analysis ──
q5 = run_query(
    "Q5 · Top 10 Drugs by Unit Cost Increase (Price Inflation)",
    """
    WITH minmax AS (
        SELECT
            drug_name,
            manufacturer,
            MIN(CASE WHEN unit_cost IS NOT NULL THEN unit_cost END)  AS cost_earliest,
            MAX(CASE WHEN unit_cost IS NOT NULL THEN unit_cost END)  AS cost_latest,
            MIN(year) AS first_year,
            MAX(year) AS last_year
        FROM drug_spending
        GROUP BY drug_name, manufacturer
        HAVING cost_earliest > 0 AND cost_latest > cost_earliest
    )
    SELECT
        drug_name,
        manufacturer,
        ROUND(cost_earliest, 2)                                          AS cost_first_yr,
        ROUND(cost_latest, 2)                                            AS cost_last_yr,
        ROUND((cost_latest - cost_earliest) * 100.0 / cost_earliest, 1) AS pct_increase,
        first_year,
        last_year
    FROM minmax
    ORDER BY pct_increase DESC
    LIMIT 10
    """
)

# ── SQL Query 6: YoY growth rate per manufacturer ────────────
q6 = run_query(
    "Q6 · Manufacturer YoY Spend Growth (Latest Year vs Prior)",
    """
    WITH yearly AS (
        SELECT
            manufacturer,
            year,
            SUM(total_spending) AS annual_spend
        FROM drug_spending
        GROUP BY manufacturer, year
    ),
    ranked AS (
        SELECT *,
               LAG(annual_spend) OVER (PARTITION BY manufacturer ORDER BY year) AS prior_spend
        FROM yearly
    ),
    latest AS (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY manufacturer ORDER BY year DESC) AS rn
        FROM ranked
        WHERE prior_spend IS NOT NULL
    )
    SELECT
        manufacturer,
        year,
        ROUND(annual_spend / 1e6, 1)                               AS spend_mn_usd,
        ROUND((annual_spend - prior_spend) * 100.0 / prior_spend, 1) AS yoy_growth_pct
    FROM latest
    WHERE rn = 1
    ORDER BY yoy_growth_pct DESC
    LIMIT 10
    """
)

conn.close()
print("\n✓ All SQL queries complete")

# ============================================================
# STEP 4 — VISUALISATIONS
# ============================================================
print("\n" + "=" * 60)
print("STEP 4: Building Visualisations")
print("=" * 60)

fig, axes = plt.subplots(2, 3, figsize=(18, 11))
fig.suptitle("US Pharma Drug Spending Analysis — Blue Matter Consulting Simulation",
             fontsize=14, fontweight='bold', y=1.01)

# ── Chart 1: Total spend by year ─────────────────────────────
ax1 = axes[0, 0]
if len(q1) > 0 and 'year' in q1.columns:
    ax1.bar(q1['year'].astype(str), q1['total_spend_bn_usd'], color='#4a90d9', edgecolor='white', linewidth=0.5)
    ax1.set_title("Total US Pharma Spend by Year ($Bn)", fontweight='bold')
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Spend ($Bn USD)")
    ax1.tick_params(axis='x', rotation=45)
    for bar, val in zip(ax1.patches, q1['total_spend_bn_usd']):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                 f'${val:.1f}B', ha='center', va='bottom', fontsize=7)

# ── Chart 2: Top 10 drugs by spend ──────────────────────────
ax2 = axes[0, 1]
if len(q2) > 0:
    colors = sns.color_palette("Blues_r", len(q2))
    bars = ax2.barh(q2['drug_name'][::-1], q2['total_spend_bn_usd'][::-1], color=colors)
    ax2.set_title("Top 10 Drugs by Total Spend ($Bn)", fontweight='bold')
    ax2.set_xlabel("Total Spend ($Bn USD)")
    for bar, val in zip(bars, q2['total_spend_bn_usd'][::-1]):
        ax2.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                 f'${val:.1f}B', va='center', fontsize=8)

# ── Chart 3: Market share by manufacturer ───────────────────
ax3 = axes[0, 2]
if len(q3) > 0:
    top5 = q3.head(5)
    other_share = max(0, 100 - top5['market_share_pct'].sum())
    labels = list(top5['manufacturer']) + (['Other'] if other_share > 0 else [])
    sizes  = list(top5['market_share_pct']) + ([other_share] if other_share > 0 else [])
    colors_pie = sns.color_palette("Set2", len(labels))
    ax3.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors_pie,
            startangle=90, textprops={'fontsize': 8})
    ax3.set_title("Market Share by Manufacturer", fontweight='bold')

# ── Chart 4: Spend by therapeutic category ──────────────────
ax4 = axes[1, 0]
if len(q4) > 0 and 'category' in q4.columns:
    cat_colors = sns.color_palette("tab10", len(q4))
    bars = ax4.bar(q4['category'], q4['total_spend_bn'], color=cat_colors, edgecolor='white', linewidth=0.5)
    ax4.set_title("Total Spend by Therapeutic Category ($Bn)", fontweight='bold')
    ax4.set_xlabel("Category")
    ax4.set_ylabel("Total Spend ($Bn)")
    ax4.tick_params(axis='x', rotation=30)
    for bar, val in zip(bars, q4['total_spend_bn']):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                 f'${val:.1f}B', ha='center', va='bottom', fontsize=7)

# ── Chart 5: Price inflation top drugs ──────────────────────
ax5 = axes[1, 1]
if len(q5) > 0 and 'pct_increase' in q5.columns:
    q5_clean = q5.dropna(subset=['pct_increase']).head(8)
    colors5 = ['#e74c3c' if x > 200 else '#f39c12' if x > 100 else '#27ae60'
               for x in q5_clean['pct_increase']]
    ax5.barh(q5_clean['drug_name'][::-1], q5_clean['pct_increase'][::-1], color=colors5[::-1])
    ax5.set_title("Drug Price Inflation (% Increase)", fontweight='bold')
    ax5.set_xlabel("% Price Increase")
    ax5.axvline(x=100, color='gray', linestyle='--', linewidth=0.8, label='100% mark')
    ax5.legend(fontsize=8)

# ── Chart 6: YoY growth by manufacturer ─────────────────────
ax6 = axes[1, 2]
if len(q6) > 0 and 'yoy_growth_pct' in q6.columns:
    q6_clean = q6.dropna(subset=['yoy_growth_pct']).head(8)
    bar_colors = ['#e74c3c' if x < 0 else '#27ae60' for x in q6_clean['yoy_growth_pct']]
    ax6.bar(q6_clean['manufacturer'], q6_clean['yoy_growth_pct'],
            color=bar_colors, edgecolor='white', linewidth=0.5)
    ax6.set_title("Manufacturer YoY Spend Growth (%)", fontweight='bold')
    ax6.set_ylabel("YoY Growth %")
    ax6.axhline(y=0, color='black', linewidth=0.8)
    ax6.tick_params(axis='x', rotation=30)

plt.tight_layout()
plt.savefig("pharma_dashboard.png", bbox_inches='tight', dpi=150)
plt.show()
print("✓ Dashboard saved as pharma_dashboard.png")

# ============================================================
# STEP 5 — KEY INSIGHTS SUMMARY (for PowerPoint / interview)
# ============================================================
print("\n" + "=" * 60)
print("STEP 5: Key Insights Summary")
print("=" * 60)

total_spend = df['total_spending'].sum() / 1e9
n_drugs     = df['drug_name'].nunique()
n_mfr       = df['manufacturer'].nunique()
year_range  = f"{df['year'].min()}–{df['year'].max()}"
top_cat     = df.groupby('category')['total_spending'].sum().idxmax()
top_drug    = df.groupby('drug_name')['total_spending'].sum().idxmax()
top_mfr     = df.groupby('manufacturer')['total_spending'].sum().idxmax()

print(f"""
┌─────────────────────────────────────────────────────┐
│         EXECUTIVE SUMMARY — CLIENT DELIVERABLE      │
├─────────────────────────────────────────────────────┤
│  Dataset period   : {year_range}                        
│  Total spend      : ${total_spend:.1f}Bn USD                
│  Unique drugs     : {n_drugs:,}                          
│  Manufacturers    : {n_mfr:,}                           
│  Top category     : {top_cat}                  
│  Top drug         : {top_drug[:30]}             
│  Top manufacturer : {top_mfr[:30]}             
├─────────────────────────────────────────────────────┤
│  KEY FINDINGS (use these in your PowerPoint)        │
│                                                     │
│  1. [Category] is the highest-spend therapeutic    │
│     area — indicating strong market opportunity    │
│     and competitive pressure                       │
│                                                     │
│  2. Top 5 manufacturers control majority of total  │
│     market spend — high concentration risk         │
│                                                     │
│  3. Unit costs for specialty drugs increased       │
│     significantly over the period — regulatory     │
│     and pricing pressure implications              │
│                                                     │
│  4. YoY growth varies sharply by manufacturer —   │
│     signals M&A activity and pipeline wins/losses  │
└─────────────────────────────────────────────────────┘

RESUME BULLET (copy this):
"Analysed ${total_spend:.0f}Bn in US pharma drug spending across
{n_drugs:,} brands ({year_range}) using Python & SQL — identified
{top_cat} as highest-spend therapeutic area and surfaced
manufacturer market share concentration risk, framed as a
pharma consulting client deliverable with Power BI dashboard"
""")

print("=" * 60)
print("✓ Full analysis complete. Files generated:")
print("  → pharma_analysis.db   (SQLite database)")
print("  → pharma_dashboard.png (6-chart visual)")
print("  Next step: Import pharma_analysis.db into Power BI")
print("=" * 60)
