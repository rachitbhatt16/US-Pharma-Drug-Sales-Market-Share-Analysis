-- ============================================================
-- US Pharma Drug Sales & Market Share Analysis
-- Dataset: FDA Medicare Drug Spending (Kaggle)
-- Author: Rachit Bhatt | MBA Finance & Business Analytics, DTU
-- Tool: SQLite / PostgreSQL / MySQL compatible
-- ============================================================
-- HOW TO USE:
-- 1. Run fda_drug_spending_analysis.py first to generate
--    pharma_analysis.db with clean data loaded
-- 2. Open pharma_analysis.db in DB Browser for SQLite or DBeaver
-- 3. Run each query block individually
-- ============================================================


-- ============================================================
-- QUERY 1: TOTAL US PHARMA MARKET SPEND BY YEAR
-- Business Question: How has total drug spending trended over time?
-- Insight: Identifies market growth rate and inflection points
-- ============================================================

SELECT
    year,
    ROUND(SUM(total_spending) / 1e9, 2)        AS total_spend_bn_usd,
    COUNT(DISTINCT drug_name)                   AS unique_drugs,
    ROUND(AVG(unit_cost), 2)                    AS avg_unit_cost_usd,
    ROUND(SUM(total_claims) / 1e6, 2)           AS total_claims_mn
FROM drug_spending
GROUP BY year
ORDER BY year ASC;


-- ============================================================
-- QUERY 2: TOP 10 DRUGS BY TOTAL CUMULATIVE SPEND
-- Business Question: Which drugs drive the most revenue?
-- Insight: Identifies blockbuster drugs and patent cliff risks
-- ============================================================

SELECT
    drug_name,
    manufacturer,
    category,
    ROUND(SUM(total_spending) / 1e9, 2)         AS total_spend_bn_usd,
    ROUND(AVG(unit_cost), 2)                     AS avg_unit_cost_usd,
    COUNT(DISTINCT year)                         AS years_on_market
FROM drug_spending
GROUP BY drug_name, manufacturer, category
ORDER BY total_spend_bn_usd DESC
LIMIT 10;


-- ============================================================
-- QUERY 3: MANUFACTURER MARKET SHARE ANALYSIS
-- Business Question: Which manufacturers dominate the US pharma market?
-- Insight: Concentration risk — top 5 vs rest of market
-- ============================================================

WITH total_market AS (
    SELECT SUM(total_spending) AS grand_total
    FROM drug_spending
),
manufacturer_spend AS (
    SELECT
        manufacturer,
        SUM(total_spending)              AS total_spend,
        COUNT(DISTINCT drug_name)        AS drug_portfolio_size,
        COUNT(DISTINCT year)             AS years_active
    FROM drug_spending
    GROUP BY manufacturer
)
SELECT
    manufacturer,
    ROUND(total_spend / 1e9, 2)                                             AS spend_bn_usd,
    ROUND(total_spend * 100.0 / (SELECT grand_total FROM total_market), 2)  AS market_share_pct,
    drug_portfolio_size,
    years_active,
    CASE
        WHEN total_spend * 100.0 / (SELECT grand_total FROM total_market) >= 10 THEN 'Tier 1 - Dominant'
        WHEN total_spend * 100.0 / (SELECT grand_total FROM total_market) >= 5  THEN 'Tier 2 - Major'
        WHEN total_spend * 100.0 / (SELECT grand_total FROM total_market) >= 1  THEN 'Tier 3 - Mid-size'
        ELSE 'Tier 4 - Niche'
    END AS market_tier
FROM manufacturer_spend
ORDER BY spend_bn_usd DESC
LIMIT 15;


-- ============================================================
-- QUERY 4: THERAPEUTIC CATEGORY BENCHMARKING
-- Business Question: Which disease areas drive the most spend?
-- Insight: Informs R&D investment and sales force allocation
-- ============================================================

WITH category_yearly AS (
    SELECT
        category,
        year,
        SUM(total_spending)         AS annual_spend,
        COUNT(DISTINCT drug_name)   AS drugs_in_category
    FROM drug_spending
    GROUP BY category, year
),
category_summary AS (
    SELECT
        category,
        SUM(annual_spend)           AS total_spend,
        AVG(annual_spend)           AS avg_annual_spend,
        MIN(annual_spend)           AS min_year_spend,
        MAX(annual_spend)           AS max_year_spend,
        MAX(drugs_in_category)      AS peak_drug_count
    FROM category_yearly
    GROUP BY category
)
SELECT
    category,
    ROUND(total_spend / 1e9, 2)         AS total_spend_bn_usd,
    ROUND(avg_annual_spend / 1e6, 2)    AS avg_annual_spend_mn,
    peak_drug_count                      AS drugs_at_peak,
    ROUND(
        (max_year_spend - min_year_spend) * 100.0 / NULLIF(min_year_spend, 0),
    1)                                   AS spend_growth_pct
FROM category_summary
ORDER BY total_spend_bn_usd DESC;


-- ============================================================
-- QUERY 5: DRUG PRICE INFLATION ANALYSIS
-- Business Question: Which drugs have seen the sharpest price increases?
-- Insight: Regulatory & pricing pressure — key risk for payers
-- ============================================================

WITH price_timeline AS (
    SELECT
        drug_name,
        manufacturer,
        category,
        MIN(year)                                           AS first_year,
        MAX(year)                                           AS last_year,
        MIN(CASE WHEN unit_cost > 0 THEN unit_cost END)    AS cost_at_entry,
        MAX(unit_cost)                                      AS cost_at_peak
    FROM drug_spending
    WHERE unit_cost IS NOT NULL AND unit_cost > 0
    GROUP BY drug_name, manufacturer, category
    HAVING cost_at_entry > 0 AND cost_at_peak > cost_at_entry
)
SELECT
    drug_name,
    manufacturer,
    category,
    first_year,
    last_year,
    ROUND(cost_at_entry, 2)                                             AS cost_at_entry_usd,
    ROUND(cost_at_peak, 2)                                              AS cost_at_peak_usd,
    ROUND((cost_at_peak - cost_at_entry) * 100.0 / cost_at_entry, 1)   AS price_increase_pct,
    CASE
        WHEN (cost_at_peak - cost_at_entry) * 100.0 / cost_at_entry >= 300 THEN 'Extreme (300%+)'
        WHEN (cost_at_peak - cost_at_entry) * 100.0 / cost_at_entry >= 100 THEN 'High (100-300%)'
        WHEN (cost_at_peak - cost_at_entry) * 100.0 / cost_at_entry >= 50  THEN 'Moderate (50-100%)'
        ELSE 'Low (<50%)'
    END AS inflation_tier
FROM price_timeline
ORDER BY price_increase_pct DESC
LIMIT 15;


-- ============================================================
-- QUERY 6: MANUFACTURER YoY SPEND GROWTH (WINDOW FUNCTION)
-- Business Question: Which manufacturers are growing or declining?
-- Insight: Signals pipeline wins, patent cliffs, biosimilar entry
-- ============================================================

WITH yearly_spend AS (
    SELECT
        manufacturer,
        year,
        SUM(total_spending)     AS annual_spend
    FROM drug_spending
    GROUP BY manufacturer, year
),
with_lag AS (
    SELECT
        manufacturer,
        year,
        annual_spend,
        LAG(annual_spend) OVER (
            PARTITION BY manufacturer ORDER BY year
        )                       AS prior_year_spend
    FROM yearly_spend
),
growth_calc AS (
    SELECT
        manufacturer,
        year,
        ROUND(annual_spend / 1e6, 1)                                        AS spend_mn_usd,
        ROUND(prior_year_spend / 1e6, 1)                                    AS prior_spend_mn_usd,
        ROUND(
            (annual_spend - prior_year_spend) * 100.0 / NULLIF(prior_year_spend, 0),
        1)                                                                   AS yoy_growth_pct
    FROM with_lag
    WHERE prior_year_spend IS NOT NULL
),
latest_year AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY manufacturer ORDER BY year DESC) AS rn
    FROM growth_calc
)
SELECT
    manufacturer,
    year            AS latest_year,
    spend_mn_usd,
    prior_spend_mn_usd,
    yoy_growth_pct,
    CASE
        WHEN yoy_growth_pct >= 20  THEN 'High Growth'
        WHEN yoy_growth_pct >= 5   THEN 'Moderate Growth'
        WHEN yoy_growth_pct >= 0   THEN 'Stable'
        WHEN yoy_growth_pct >= -10 THEN 'Declining'
        ELSE 'Sharp Decline'
    END AS growth_category
FROM latest_year
WHERE rn = 1
ORDER BY yoy_growth_pct DESC
LIMIT 15;


-- ============================================================
-- QUERY 7: DRUG PORTFOLIO DEPTH BY MANUFACTURER
-- Business Question: Which manufacturers have the broadest portfolios?
-- Insight: Diversification vs single-blockbuster risk
-- ============================================================

SELECT
    manufacturer,
    COUNT(DISTINCT drug_name)                                           AS total_drugs,
    COUNT(DISTINCT category)                                            AS therapeutic_areas,
    ROUND(SUM(total_spending) / 1e9, 2)                                AS total_spend_bn,
    ROUND(SUM(total_spending) / COUNT(DISTINCT drug_name) / 1e6, 1)   AS avg_spend_per_drug_mn
FROM drug_spending
GROUP BY manufacturer
HAVING total_drugs >= 3
ORDER BY total_drugs DESC
LIMIT 12;


-- ============================================================
-- QUERY 8: YoY CATEGORY GROWTH TREND (last 3 years)
-- Business Question: Which categories are accelerating vs plateauing?
-- Insight: Forward-looking market opportunity sizing
-- ============================================================

WITH cat_year AS (
    SELECT
        category,
        year,
        SUM(total_spending) AS spend
    FROM drug_spending
    GROUP BY category, year
),
cat_growth AS (
    SELECT
        category,
        year,
        spend,
        LAG(spend) OVER (PARTITION BY category ORDER BY year) AS prior_spend
    FROM cat_year
)
SELECT
    category,
    year,
    ROUND(spend / 1e6, 1)                                               AS spend_mn_usd,
    ROUND(
        (spend - prior_spend) * 100.0 / NULLIF(prior_spend, 0),
    1)                                                                   AS yoy_growth_pct
FROM cat_growth
WHERE prior_spend IS NOT NULL
  AND year >= (SELECT MAX(year) - 3 FROM drug_spending)
ORDER BY category, year;


-- ============================================================
-- EXECUTIVE SUMMARY — for Power BI import or stakeholder reporting
-- ============================================================

SELECT 'Total Market Spend (Bn USD)'   AS metric, ROUND(SUM(total_spending) / 1e9, 1) AS value FROM drug_spending
UNION ALL
SELECT 'Unique Drugs Analysed',         COUNT(DISTINCT drug_name)   FROM drug_spending
UNION ALL
SELECT 'Unique Manufacturers',          COUNT(DISTINCT manufacturer) FROM drug_spending
UNION ALL
SELECT 'Years Covered',                 COUNT(DISTINCT year)         FROM drug_spending
UNION ALL
SELECT 'Avg Unit Cost (USD)',           ROUND(AVG(unit_cost), 2)     FROM drug_spending WHERE unit_cost > 0
UNION ALL
SELECT 'Total Claims (Mn)',             ROUND(SUM(total_claims) / 1e6, 1) FROM drug_spending WHERE total_claims IS NOT NULL;
