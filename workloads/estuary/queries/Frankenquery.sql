-- Step 1: Analyze Supplier Delivery Performance
WITH supplier_delivery_metrics AS (
	SELECT
		s.s_suppkey,
		s.s_name,
		s.s_nationkey,
		s.s_acctbal,
		s.s_address,
		s.s_phone,
		COUNT(DISTINCT l.l_orderkey) AS total_orders,
		AVG(DAYS_BETWEEN(l.l_receiptdate, l.l_commitdate)) AS avg_delivery_delay,
		MEDIAN(DAYS_BETWEEN(l.l_receiptdate, l.l_commitdate)) AS median_delivery_delay,
		PERCENTILE_DISC(0.90) WITHIN GROUP(ORDER BY DAYS_BETWEEN(l.l_receiptdate, l.l_commitdate)) AS p90_delivery_delay,
		SUM(CASE WHEN l.l_receiptdate > l.l_commitdate THEN 1 ELSE 0 END) AS late_deliveries,
		SUM(CASE WHEN l.l_receiptdate <= l.l_commitdate THEN 1 ELSE 0 END) AS on_time_deliveries,
		SUM(CASE WHEN DAYS_BETWEEN(l.l_receiptdate, l.l_commitdate) > 7 THEN 1 ELSE 0 END) AS severely_late_deliveries,
		SUM(l.l_extendedprice * (1 - l.l_discount)) AS total_revenue,
		SUM(l.l_extendedprice * (1 - l.l_discount) * l.l_tax) AS total_tax,
		SUM(l.l_quantity) AS total_quantity,
		AVG(l.l_discount) AS avg_discount_rate,
		MAX(l.l_discount) AS max_discount_offered,
		STDDEV(l.l_extendedprice * (1 - l.l_discount)) AS revenue_volatility,
		VARIANCE(l.l_extendedprice * (1 - l.l_discount)) AS revenue_variance,
		MIN(l.l_shipdate) AS first_shipment_date,
		MAX(l.l_shipdate) AS last_shipment_date,
		DAYS_BETWEEN(MAX(l.l_shipdate), MIN(l.l_shipdate)) AS active_days,
		COUNT(DISTINCT l.l_partkey) AS unique_parts_shipped
	FROM supplier s
	JOIN lineitem l ON s.s_suppkey = l.l_suppkey
	GROUP BY s.s_suppkey, s.s_name, s.s_nationkey, s.s_acctbal, s.s_address, s.s_phone
),

-- Step 2: Calculate Supplier Transaction Frequency Patterns
supplier_transaction_frequency_p1 AS (
	SELECT
		l_suppkey,
		DATE_TRUNC('MONTH', l_shipdate) AS ship_month,
		COUNT(*) AS transactions_per_month,
		SUM(l_quantity) AS quantity_per_month,
		SUM(l_extendedprice * (1 - l_discount)) AS revenue_per_month,
		LAG(COUNT(*)) OVER (PARTITION BY l_suppkey ORDER BY DATE_TRUNC('MONTH', l_shipdate)) AS prev_month_transactions,
		LAG(SUM(l_quantity)) OVER (PARTITION BY l_suppkey ORDER BY DATE_TRUNC('MONTH', l_shipdate)) AS prev_month_quantity,
		LAG(SUM(l_extendedprice * (1 - l_discount))) OVER (PARTITION BY l_suppkey ORDER BY DATE_TRUNC('MONTH', l_shipdate)) AS prev_month_revenue,
		LAG(DATE_TRUNC('MONTH', l_shipdate)) OVER (PARTITION BY l_suppkey ORDER BY DATE_TRUNC('MONTH', l_shipdate)) as prev_ship_month
	FROM lineitem
	GROUP BY l_suppkey, DATE_TRUNC('MONTH', l_shipdate)
),

supplier_transaction_frequency AS (
	SELECT
		p1.*,
		DAYS_BETWEEN(ship_month, prev_ship_month) AS months_since_last_activity
	FROM supplier_transaction_frequency_p1 as p1
),

-- Step 3: Calculate Seasonal Ordering Patterns (Quarterly)
seasonal_patterns_quarterly AS (
	SELECT
		l.l_suppkey,
		TO_CHAR(o.o_orderdate, 'Q') AS quarter,
		YEAR(o.o_orderdate) AS "year",
		COUNT(DISTINCT o.o_orderkey) AS quarterly_orders,
		COUNT(DISTINCT MONTH(o.o_orderdate)) AS active_months_in_quarter,
		SUM(l.l_quantity) AS quarterly_quantity,
		SUM(l.l_extendedprice * (1 - l.l_discount)) AS quarterly_revenue,
		AVG(l.l_extendedprice * (1 - l.l_discount)) AS avg_order_value_in_quarter,
		COUNT(DISTINCT l.l_partkey) AS unique_parts_in_quarter,
		LAG(SUM(l.l_quantity)) OVER (PARTITION BY l.l_suppkey, TO_CHAR(o.o_orderdate, 'Q') ORDER BY YEAR(o.o_orderdate)) AS prev_year_quarterly_quantity,
		LAG(SUM(l.l_extendedprice * (1 - l.l_discount))) OVER (PARTITION BY l.l_suppkey, TO_CHAR(o.o_orderdate, 'Q') ORDER BY YEAR(o.o_orderdate)) AS prev_year_quarterly_revenue
	FROM lineitem l
	JOIN orders o ON l.l_orderkey = o.o_orderkey
	GROUP BY l.l_suppkey, TO_CHAR(o.o_orderdate, 'Q'), YEAR(o.o_orderdate)
),

-- Step 4: Calculate Seasonal Ordering Patterns (Monthly)
seasonal_patterns_monthly AS (
	SELECT
		l.l_suppkey,
		MONTH(o.o_orderdate) AS "month",
		YEAR(o.o_orderdate) AS "year",
		COUNT(DISTINCT o.o_orderkey) AS monthly_orders,
		SUM(l.l_quantity) AS monthly_quantity,
		SUM(l.l_extendedprice * (1 - l.l_discount)) AS monthly_revenue,
		LAG(SUM(l.l_quantity)) OVER (PARTITION BY l.l_suppkey, MONTH(o.o_orderdate) ORDER BY YEAR(o.o_orderdate)) AS prev_year_monthly_quantity,
		LAG(SUM(l.l_extendedprice * (1 - l.l_discount))) OVER (PARTITION BY l.l_suppkey, MONTH(o.o_orderdate) ORDER BY YEAR(o.o_orderdate)) AS prev_year_monthly_revenue
	FROM lineitem l
	JOIN orders o ON l.l_orderkey = o.o_orderkey
	GROUP BY l.l_suppkey, MONTH(o.o_orderdate), YEAR(o.o_orderdate)
),

-- Step 5: Calculate YoY Growth and Seasonality Scores (Quarterly)
supplier_seasonality_quarterly AS (
	SELECT
		l_suppkey,
		quarter,
		"year",
		quarterly_quantity,
		quarterly_revenue,
		unique_parts_in_quarter,
		active_months_in_quarter,
		CASE
			WHEN prev_year_quarterly_quantity > 0 THEN (quarterly_quantity - prev_year_quarterly_quantity) / prev_year_quarterly_quantity * 100
			ELSE NULL
		END AS yoy_quantity_growth,
		CASE
			WHEN prev_year_quarterly_revenue > 0 THEN (quarterly_revenue - prev_year_quarterly_revenue) / prev_year_quarterly_revenue * 100
			ELSE NULL
		END AS yoy_revenue_growth,
		DENSE_RANK() OVER (PARTITION BY l_suppkey ORDER BY quarterly_quantity DESC) AS quantity_quarter_rank,
		DENSE_RANK() OVER (PARTITION BY l_suppkey ORDER BY quarterly_revenue DESC) AS revenue_quarter_rank,
		quarterly_quantity / NULLIF(quarterly_orders, 0) AS avg_quantity_per_order,
		quarterly_revenue / NULLIF(quarterly_orders, 0) AS avg_revenue_per_order
	FROM seasonal_patterns_quarterly
),

-- Step 6: Calculate YoY Growth and Seasonality Scores (Monthly)
supplier_seasonality_monthly AS (
	SELECT
		l_suppkey,
		"month",
		"year",
		monthly_quantity,
		monthly_revenue,
		CASE
			WHEN prev_year_monthly_quantity > 0 THEN (monthly_quantity - prev_year_monthly_quantity) / prev_year_monthly_quantity * 100
			ELSE NULL
		END AS yoy_quantity_growth_monthly,
		CASE
			WHEN prev_year_monthly_revenue > 0 THEN (monthly_revenue - prev_year_monthly_revenue) / prev_year_monthly_revenue * 100
			ELSE NULL
		END AS yoy_revenue_growth_monthly,
		DENSE_RANK() OVER (PARTITION BY l_suppkey ORDER BY monthly_quantity DESC) AS quantity_month_rank,
		DENSE_RANK() OVER (PARTITION BY l_suppkey ORDER BY monthly_revenue DESC) AS revenue_month_rank
	FROM seasonal_patterns_monthly
),

-- Step 7: Analyze Parts Supply Chain Diversification
part_supplier_diversity AS (
	SELECT
		p.p_partkey,
		p.p_name,
		p.p_mfgr,
		p.p_brand,
		p.p_type,
		p.p_size,
		p.p_container,
		p.p_retailprice,
		COUNT(DISTINCT ps.ps_suppkey) AS supplier_count,
		MAX(ps.ps_supplycost) / NULLIF(MIN(ps.ps_supplycost), 0) AS cost_ratio,
		MAX(ps.ps_supplycost) - MIN(ps.ps_supplycost) AS cost_spread,
		STDDEV(ps.ps_supplycost) AS cost_volatility,
		AVG(ps.ps_supplycost) AS avg_cost,
		MIN(ps.ps_supplycost) AS min_cost,
		MAX(ps.ps_supplycost) AS max_cost,
		AVG(ps.ps_availqty) AS avg_availability,
		SUM(ps.ps_availqty) AS total_availability,
		MIN(ps.ps_availqty) AS min_availability,
		MAX(ps.ps_availqty) AS max_availability,
		VARIANCE(ps.ps_availqty) AS availability_variance
	FROM part p
	JOIN partsupp ps ON p.p_partkey = ps.ps_partkey
	GROUP BY p.p_partkey, p.p_name, p.p_mfgr, p.p_brand, p.p_type, p.p_size, p.p_container, p.p_retailprice
	HAVING COUNT(DISTINCT ps.ps_suppkey) > 1
),

-- Step 8: Analyze Part Categories and Their Supply Chain Characteristics
part_category_analysis AS (
	SELECT
		regexp_substr(p.p_type, '[^ ]*') AS part_category,
		COUNT(DISTINCT p.p_partkey) AS category_part_count,
		AVG(psd.supplier_count) AS avg_suppliers_per_part,
		MIN(psd.supplier_count) AS min_suppliers_per_part,
		MAX(psd.supplier_count) AS max_suppliers_per_part,
		AVG(psd.cost_ratio) AS avg_cost_ratio,
		AVG(psd.cost_volatility) AS avg_cost_volatility,
		SUM(p.p_retailprice * psd.total_availability) AS category_inventory_value,
		COUNT(DISTINCT ps.ps_suppkey) AS unique_suppliers_in_category
	FROM part p
	JOIN part_supplier_diversity psd ON p.p_partkey = psd.p_partkey
	JOIN partsupp ps ON p.p_partkey = ps.ps_partkey
	GROUP BY regexp_substr(p.p_type, '[^ ]*')
),

-- Step 9: Geographic Performance Analysis (Nation Level)
nation_performance AS (
	SELECT
		n.n_nationkey,
		n.n_name AS nation,
		n.n_regionkey,
		COUNT(DISTINCT s.s_suppkey) AS supplier_count,
		AVG(sdm.avg_delivery_delay) AS nation_avg_delay,
		MEDIAN(sdm.avg_delivery_delay) AS nation_median_delay,
		AVG(sdm.p90_delivery_delay) AS nation_p90_delay,
		SUM(sdm.total_revenue) AS nation_revenue,
		SUM(sdm.total_quantity) AS nation_quantity,
		SUM(sdm.late_deliveries) / NULLIF(SUM(sdm.total_orders), 0) * 100 AS nation_late_delivery_pct,
		SUM(sdm.severely_late_deliveries) / NULLIF(SUM(sdm.total_orders), 0) * 100 AS nation_severely_late_pct,
		AVG(sdm.revenue_volatility) AS nation_avg_rev_volatility,
		SUM(sdm.unique_parts_shipped) AS nation_unique_parts,
		COUNT(DISTINCT l.l_partkey) AS nation_distinct_parts
	FROM supplier s
	JOIN supplier_delivery_metrics sdm ON s.s_suppkey = sdm.s_suppkey
	JOIN nation n ON s.s_nationkey = n.n_nationkey
	JOIN lineitem l ON s.s_suppkey = l.l_suppkey
	GROUP BY n.n_nationkey, n.n_name, n.n_regionkey
),

-- Step 10: Geographic Performance Analysis (Region Level)
region_performance AS (
	SELECT
		r.r_regionkey,
		r.r_name AS region,
		COUNT(DISTINCT s.s_suppkey) AS supplier_count,
		COUNT(DISTINCT n.n_nationkey) AS nations_count,
		AVG(np.nation_avg_delay) AS region_avg_delay,
		AVG(np.nation_median_delay) AS region_median_delay,
		SUM(np.nation_revenue) AS region_revenue,
		SUM(np.nation_quantity) AS region_quantity,
		SUM(np.nation_unique_parts) AS region_unique_parts,
		AVG(np.nation_late_delivery_pct) AS region_late_delivery_pct,
		AVG(np.nation_severely_late_pct) AS region_severely_late_pct,
		AVG(np.nation_avg_rev_volatility) AS region_avg_rev_volatility,
		MAX(np.nation_revenue) / NULLIF(MIN(np.nation_revenue), 0) AS nation_revenue_disparity,
		STDDEV(np.nation_late_delivery_pct) AS late_delivery_pct_stddev
	FROM region r
	JOIN nation_performance np ON r.r_regionkey = np.n_regionkey
	JOIN nation n ON np.n_nationkey = n.n_nationkey
	JOIN supplier s ON n.n_nationkey = s.s_nationkey
	GROUP BY r.r_regionkey, r.r_name
),

-- Step 11: Customer Satisfaction Metrics via Order Lifecycle Analysis
customer_satisfaction AS (
	SELECT
		l.l_suppkey,
		o.o_custkey,
		COUNT(DISTINCT o.o_orderkey) AS order_count,
		AVG(DAYS_BETWEEN(l.l_receiptdate, o.o_orderdate)) AS avg_order_to_receipt,
		AVG(o.o_totalprice) AS avg_order_value,
		COUNT(DISTINCT CASE WHEN l.l_returnflag = 'R' THEN l.l_orderkey END) AS returned_orders,
		COUNT(DISTINCT CASE WHEN l.l_returnflag = 'R' THEN l.l_orderkey END) / NULLIF(COUNT(DISTINCT o.o_orderkey), 0) * 100 AS return_rate,
		AVG(CASE WHEN l.l_returnflag = 'R' THEN l.l_extendedprice * (1 - l.l_discount) ELSE NULL END) AS avg_return_value,
		COUNT(DISTINCT CASE WHEN o.o_orderstatus = 'F' THEN o.o_orderkey END) / NULLIF(COUNT(DISTINCT o.o_orderkey), 0) * 100 AS fulfillment_rate,
		COUNT(DISTINCT CASE WHEN o.o_orderpriority LIKE '1-%' OR o.o_orderpriority LIKE '2-%' THEN o.o_orderkey END) AS high_priority_orders,
		COUNT(DISTINCT CASE WHEN o.o_orderpriority LIKE '1-%' OR o.o_orderpriority LIKE '2-%' THEN o.o_orderkey END) / NULLIF(COUNT(DISTINCT o.o_orderkey), 0) * 100 AS high_priority_percentage
	FROM lineitem l
	JOIN orders o ON l.l_orderkey = o.o_orderkey
	GROUP BY l.l_suppkey, o.o_custkey
),

-- Step 12: Supplier Customer Diversity and Loyalty Analysis
supplier_customer_analysis AS (
	SELECT
		csa.l_suppkey,
		COUNT(DISTINCT csa.o_custkey) AS unique_customers,
		AVG(csa.order_count) AS avg_orders_per_customer,
		MAX(csa.order_count) AS max_orders_from_customer,
		MIN(csa.order_count) AS min_orders_from_customer,
		STDDEV(csa.order_count) AS order_count_stddev,
		COUNT(DISTINCT CASE WHEN csa.order_count > 5 THEN csa.o_custkey ELSE NULL END) AS loyal_customers,
		COUNT(DISTINCT CASE WHEN csa.order_count > 5 THEN csa.o_custkey ELSE NULL END) / NULLIF(COUNT(DISTINCT csa.o_custkey), 0) * 100 AS loyal_customer_percentage,
		AVG(csa.return_rate) AS avg_return_rate,
		MAX(csa.return_rate) AS max_return_rate,
		AVG(csa.avg_order_value) AS avg_customer_order_value,
		MAX(csa.avg_order_value) AS max_customer_order_value,
		MIN(csa.avg_order_value) AS min_customer_order_value,
		COUNT(DISTINCT CASE WHEN csa.high_priority_percentage > 50 THEN csa.o_custkey ELSE NULL END) AS high_priority_customers,
		COUNT(DISTINCT CASE WHEN csa.high_priority_percentage > 50 THEN csa.o_custkey ELSE NULL END) / NULLIF(COUNT(DISTINCT csa.o_custkey), 0) * 100 AS high_priority_customer_percentage
	FROM customer_satisfaction csa
	GROUP BY csa.l_suppkey
),

-- Step 13: Calculate Risk Scores for Each Supplier
supplier_risk_scores AS (
	SELECT
		sdm.s_suppkey,
		sdm.s_name,
		sdm.s_acctbal,
		sdm.total_orders,
		sdm.total_revenue,
		sdm.total_quantity,
		sdm.late_deliveries / NULLIF(sdm.total_orders, 0) * 100 AS late_delivery_pct,
		sdm.severely_late_deliveries / NULLIF(sdm.total_orders, 0) * 100 AS severely_late_pct,
		sdm.on_time_deliveries / NULLIF(sdm.total_orders, 0) * 100 AS on_time_delivery_pct,
		sdm.avg_delivery_delay,
		sdm.median_delivery_delay,
		sdm.p90_delivery_delay,
		sdm.revenue_volatility,
		sdm.revenue_volatility / NULLIF(sdm.total_revenue / sdm.total_orders, 0) AS normalized_volatility,
		sdm.active_days,
		sdm.unique_parts_shipped,
		sdm.avg_discount_rate,
		sdm.max_discount_offered,
		sca.unique_customers,
		sca.loyal_customer_percentage,
		sca.avg_return_rate,

		-- Risk Components:

		-- Delivery Risk Score (higher is worse): 0-100
		(sdm.late_deliveries / NULLIF(sdm.total_orders, 0) * 40) +
		(sdm.severely_late_deliveries / NULLIF(sdm.total_orders, 0) * 60) +
		(CASE WHEN sdm.avg_delivery_delay > 0 THEN LOG10(sdm.avg_delivery_delay + 1) * 10 ELSE 0 END) +
		(CASE WHEN sdm.p90_delivery_delay > 10 THEN LOG10(sdm.p90_delivery_delay) * 5 ELSE 0 END) AS delivery_risk_score,

		-- Financial Risk Score (higher is worse): 0-100
		(sdm.revenue_volatility / NULLIF(sdm.total_revenue / sdm.total_orders, 0) * 20) +
		(CASE WHEN sdm.s_acctbal < 0 THEN ABS(sdm.s_acctbal) / 1000 * 5 ELSE 0 END) +
		(CASE WHEN sdm.total_orders < 10 THEN 20 ELSE 0 END) +
		(CASE WHEN sdm.active_days < 365 THEN (365 - sdm.active_days) / 3.65 ELSE 0 END) +
		(CASE WHEN stf.months_since_last_activity IS NULL OR stf.months_since_last_activity > 6 THEN 30 ELSE stf.months_since_last_activity * 5 END) AS financial_risk_score,

		-- Diversification Risk Score (higher is worse): 0-100
		(CASE WHEN sdm.unique_parts_shipped < 5 THEN (5 - sdm.unique_parts_shipped) * 10 ELSE 0 END) +
		(CASE WHEN sca.unique_customers < 5 THEN (5 - sca.unique_customers) * 10 ELSE 0 END) +
		(CASE WHEN sca.loyal_customer_percentage < 30 THEN (30 - sca.loyal_customer_percentage) ELSE 0 END) AS diversification_risk_score,

		-- Quality Risk Score (higher is worse): 0-100
		(sca.avg_return_rate * 5) +
		(CASE WHEN sca.max_return_rate > 30 THEN (sca.max_return_rate - 30) * 2 ELSE 0 END) AS quality_risk_score
	FROM supplier_delivery_metrics sdm
	JOIN supplier_customer_analysis sca ON sdm.s_suppkey = sca.l_suppkey
	LEFT JOIN (
		SELECT
			l_suppkey,
			MIN(months_since_last_activity) AS months_since_last_activity
		FROM supplier_transaction_frequency
		WHERE months_since_last_activity IS NOT NULL
		GROUP BY l_suppkey
	) stf ON sdm.s_suppkey = stf.l_suppkey
),

-- Step 14: Aggregate Seasonal Insights per Supplier (Quarterly)
supplier_seasonality_quarterly_agg AS (
	SELECT
		ssq.l_suppkey,
		MAX(CASE WHEN ssq.quantity_quarter_rank = 1 THEN ssq.quarter ELSE NULL END) AS peak_quantity_quarter,
		MAX(CASE WHEN ssq.revenue_quarter_rank = 1 THEN ssq.quarter ELSE NULL END) AS peak_revenue_quarter,
		AVG(CASE WHEN ssq.yoy_quantity_growth IS NOT NULL THEN ABS(ssq.yoy_quantity_growth) ELSE NULL END) AS avg_quantity_volatility,
		AVG(CASE WHEN ssq.yoy_revenue_growth IS NOT NULL THEN ABS(ssq.yoy_revenue_growth) ELSE NULL END) AS avg_revenue_volatility,
		MAX(ssq.yoy_revenue_growth) AS max_revenue_growth,
		MIN(ssq.yoy_revenue_growth) AS min_revenue_growth,
		AVG(ssq.unique_parts_in_quarter) AS avg_unique_parts_per_quarter,
		MAX(ssq.active_months_in_quarter) AS max_active_months_in_quarter,
		AVG(ssq.avg_quantity_per_order) AS overall_avg_quantity_per_order,
		AVG(ssq.avg_revenue_per_order) AS overall_avg_revenue_per_order,
		STDDEV(ssq.quarterly_revenue) / NULLIF(AVG(ssq.quarterly_revenue), 0) * 100 AS revenue_coefficient_of_variation
	FROM supplier_seasonality_quarterly ssq
	GROUP BY ssq.l_suppkey
),

-- Step 15: Aggregate Seasonal Insights per Supplier (Monthly)
supplier_seasonality_monthly_agg AS (
	SELECT
		ssm.l_suppkey,
		MAX(CASE WHEN ssm.quantity_month_rank = 1 THEN ssm."month" ELSE NULL END) AS peak_quantity_month,
		MAX(CASE WHEN ssm.revenue_month_rank = 1 THEN ssm."month" ELSE NULL END) AS peak_revenue_month,
		AVG(CASE WHEN ssm.yoy_quantity_growth_monthly IS NOT NULL THEN ABS(ssm.yoy_quantity_growth_monthly) ELSE NULL END) AS avg_monthly_quantity_volatility,
		AVG(CASE WHEN ssm.yoy_revenue_growth_monthly IS NOT NULL THEN ABS(ssm.yoy_revenue_growth_monthly) ELSE NULL END) AS avg_monthly_revenue_volatility,
		MAX(ssm.yoy_revenue_growth_monthly) AS max_monthly_revenue_growth,
		MIN(ssm.yoy_revenue_growth_monthly) AS min_monthly_revenue_growth,
		STDDEV(ssm.monthly_revenue) / NULLIF(AVG(ssm.monthly_revenue), 0) * 100 AS monthly_revenue_coefficient_of_variation
	FROM supplier_seasonality_monthly ssm
	GROUP BY ssm.l_suppkey
),

-- Step 16: Parts Supplied Analysis
supplier_parts_profile AS (
		SELECT
		ps.ps_suppkey,
		COUNT(DISTINCT ps.ps_partkey) AS unique_parts_supplied,
		COUNT(DISTINCT p.p_mfgr) AS manufacturer_count,
		COUNT(DISTINCT p.p_brand) AS brand_count,
		COUNT(DISTINCT regexp_substr(p.p_type, '[^ ]*')) AS part_category_count,
		AVG(ps.ps_supplycost) AS avg_supply_cost,
		MIN(ps.ps_supplycost) AS min_supply_cost,
		MAX(ps.ps_supplycost) AS max_supply_cost,
		STDDEV(ps.ps_supplycost) AS supply_cost_stddev,
		SUM(ps.ps_availqty) AS total_availability,
		MIN(ps.ps_availqty) AS min_availability,
		MAX(ps.ps_availqty) AS max_availability,
		AVG(ps.ps_availqty) AS avg_availability,
		STDDEV(ps.ps_availqty) AS availability_stddev,
		AVG(ps.ps_availqty * p.p_retailprice) AS avg_inventory_value,
		SUM(ps.ps_availqty * p.p_retailprice) AS total_inventory_value,
		COUNT(DISTINCT regexp_substr(p.p_type, '[^ ]*')) AS category_diversity,
		AVG(CASE WHEN psd.supplier_count IS NOT NULL THEN psd.supplier_count ELSE 1 END) AS avg_supply_chain_redundancy,
		SUM(CASE WHEN p.p_retailprice > 1000 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) * 100 AS premium_part_percentage,
		SUM(ps.ps_availqty) / NULLIF(SUM(COALESCE(l.l_quantity, 0)), 0) AS inventory_turnover_ratio
	FROM partsupp ps
	JOIN part p ON ps.ps_partkey = p.p_partkey
	LEFT JOIN part_supplier_diversity psd ON p.p_partkey = psd.p_partkey
	LEFT JOIN lineitem l ON ps.ps_suppkey = l.l_suppkey
	GROUP BY ps.ps_suppkey
),

-- Step 17: Text Analysis of Supplier Comments
supplier_comment_analysis AS (
	SELECT
		s_suppkey,
		s_comment,
		LENGTH(s_comment) AS comment_length,
		LENGTH(REGEXP_REPLACE(LOWER(s_comment), '[^(quality|reliable|good|excellent|best|quick|fast|prompt|timely|superior)]', '')) AS positive_mentions,
		LENGTH(REGEXP_REPLACE(LOWER(s_comment), '[^(delay|issue|problem|complaint|late|bad|slow|poor|dissatisfied|disappointed)]', '')) AS negative_mentions,
		CASE
			WHEN LENGTH(REGEXP_REPLACE(LOWER(s_comment), '[^(quality|reliable|good|excellent|best|quick|fast|prompt|timely|superior)]', '')) >
				LENGTH(REGEXP_REPLACE(LOWER(s_comment), '[^(delay|issue|problem|complaint|late|bad|slow|poor|dissatisfied|disappointed)]', '')) THEN 'Positive'
			WHEN LENGTH(REGEXP_REPLACE(LOWER(s_comment), '[^(quality|reliable|good|excellent|best|quick|fast|prompt|timely|superior)]', '')) <
				LENGTH(REGEXP_REPLACE(LOWER(s_comment), '[^(delay|issue|problem|complaint|late|bad|slow|poor|dissatisfied|disappointed)]', '')) THEN 'Negative'
			ELSE 'Neutral'
		END AS sentiment,
		LENGTH(REGEXP_REPLACE(LOWER(s_comment), '[^(price|cost|discount|rate|value|expense)]', '')) AS financial_mentions,
		LENGTH(REGEXP_REPLACE(LOWER(s_comment), '[^(ship|deliver|transport|carry|move|logistics)]', '')) AS logistics_mentions,
		LENGTH(REGEXP_REPLACE(LOWER(s_comment), '[^(part|item|product|stock|component|material)]', '')) AS product_mentions
	FROM supplier
),

-- Step 18: Final Supplier Performance Report
final_supplier_report AS (
	SELECT
		sdm.s_suppkey,
		sdm.s_name,
		sdm.s_nationkey,
		sdm.s_acctbal,
		sdm.s_address,
		sdm.s_phone,
		sdm.total_orders,
		sdm.avg_delivery_delay,
		sdm.median_delivery_delay,
		sdm.p90_delivery_delay,
		sdm.late_deliveries,
		sdm.on_time_deliveries,
		sdm.severely_late_deliveries,
		sdm.total_revenue,
		sdm.total_tax,
		sdm.total_quantity,
		sdm.avg_discount_rate,
		sdm.max_discount_offered,
		sdm.revenue_volatility,
		sdm.revenue_variance,
		sdm.first_shipment_date,
		sdm.last_shipment_date,
		sdm.active_days,
		sdm.unique_parts_shipped,
		stf.transactions_per_month,
		stf.quantity_per_month,
		stf.revenue_per_month,
		stf.prev_month_transactions,
		stf.prev_month_quantity,
		stf.prev_month_revenue,
		stf.months_since_last_activity,
		ssq_agg.peak_quantity_quarter,
		ssq_agg.peak_revenue_quarter,
		ssq_agg.avg_quantity_volatility,
		ssq_agg.avg_revenue_volatility,
		ssq_agg.max_revenue_growth,
		ssq_agg.min_revenue_growth,
		ssq_agg.avg_unique_parts_per_quarter,
		ssq_agg.max_active_months_in_quarter,
		ssq_agg.overall_avg_quantity_per_order,
		ssq_agg.overall_avg_revenue_per_order,
		ssq_agg.revenue_coefficient_of_variation,
		ssm_agg.peak_quantity_month,
		ssm_agg.peak_revenue_month,
		ssm_agg.avg_monthly_quantity_volatility,
		ssm_agg.avg_monthly_revenue_volatility,
		ssm_agg.max_monthly_revenue_growth,
		ssm_agg.min_monthly_revenue_growth,
		ssm_agg.monthly_revenue_coefficient_of_variation,
		srs.delivery_risk_score,
		srs.financial_risk_score,
		srs.diversification_risk_score,
		srs.quality_risk_score,
		spp.unique_parts_supplied,
		spp.manufacturer_count,
		spp.brand_count,
		spp.part_category_count,
		spp.avg_supply_cost,
		spp.min_supply_cost,
		spp.max_supply_cost,
		spp.supply_cost_stddev,
		spp.total_availability,
		spp.min_availability,
		spp.max_availability,
		spp.avg_availability,
		spp.availability_stddev,
		spp.avg_inventory_value,
		spp.total_inventory_value,
		spp.category_diversity,
		spp.avg_supply_chain_redundancy,
		spp.premium_part_percentage,
		spp.inventory_turnover_ratio,
		sca.sentiment,
		sca.comment_length,
		sca.positive_mentions,
		sca.negative_mentions,
		sca.financial_mentions,
		sca.logistics_mentions,
		sca.product_mentions
	FROM supplier_delivery_metrics sdm
	LEFT JOIN supplier_transaction_frequency stf ON sdm.s_suppkey = stf.l_suppkey
	LEFT JOIN supplier_seasonality_quarterly_agg ssq_agg ON sdm.s_suppkey = ssq_agg.l_suppkey
	LEFT JOIN supplier_seasonality_monthly_agg ssm_agg ON sdm.s_suppkey = ssm_agg.l_suppkey
	LEFT JOIN supplier_risk_scores srs ON sdm.s_suppkey = srs.s_suppkey
	LEFT JOIN supplier_parts_profile spp ON sdm.s_suppkey = spp.ps_suppkey
	LEFT JOIN supplier_comment_analysis sca ON sdm.s_suppkey = sca.s_suppkey
)

SELECT * FROM final_supplier_report LIMIT 1000;