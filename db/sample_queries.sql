-- ---------------------------------------------------------------------
-- Sample Queries
-- ---------------------------------------------------------------------

-- ---------------------------------------------------------------------
-- 1. Production Health Dashboard (AC 3)
-- This query calculates the weekly error rate per production line. It identifies which lines are struggling with efficiency by comparing planned versus actual units.
-- ---------------------------------------------------------------------
SELECT 
    pr.production_line_id,
    DATE_TRUNC('week', l.production_date) AS production_week,
    SUM(pr.units_planned) AS total_planned,
    SUM(pr.units_actual) AS total_actual,
    SUM(pr.units_planned - pr.units_actual) AS total_errors,
    ROUND(
        CAST(SUM(pr.units_planned - pr.units_actual) AS NUMERIC) / 
        NULLIF(SUM(pr.units_planned), 0) * 100, 2
    ) AS error_rate_percentage
FROM production_records pr
JOIN lots l ON pr.lot_id = l.id
GROUP BY pr.production_line_id, production_week
ORDER BY production_week DESC, error_rate_percentage DESC;

-- ---------------------------------------------------------------------
-- 2. Quality Defect Trending (AC 3)
-- This query provides a monthly breakdown of defect types. This allows analysts to see if specific issues (e.g., "Cosmetic") are increasing over time.
-- ---------------------------------------------------------------------
SELECT 
    defect_type,
    DATE_TRUNC('month', inspection_date) AS inspection_month,
    SUM(defect_count) AS total_defects,
    COUNT(DISTINCT lot_id) AS affected_lots_count
FROM quality_inspection_records
WHERE defect_type IS NOT NULL
GROUP BY defect_type, inspection_month
ORDER BY inspection_month DESC, total_defects DESC;

-- ---------------------------------------------------------------------
-- 3. Lot Status Search (AC 3)
-- A single-point lookup query for the "Search" function. It returns the current lifecycle status of a specific Lot ID across production, quality, and shipping.
-- ---------------------------------------------------------------------
SELECT 
    l.lot_code,
    l.production_date,
    CASE 
        WHEN sr.shipment_status IS NOT NULL THEN 'Shipped'
        WHEN qr.is_pass = FALSE THEN 'Failed Quality'
        WHEN l.is_pending_inspection = TRUE THEN 'Pending Inspection'
        ELSE 'In Production'
    END AS current_operational_status,
    sr.ship_date,
    sr.carrier
FROM lots l
LEFT JOIN quality_inspection_records qr ON l.id = qr.lot_id
LEFT JOIN shipping_records sr ON l.id = sr.lot_id
WHERE l.lot_code = 'LOT-20251219-003' -- Example Search Parameter
ORDER BY l.production_date DESC
LIMIT 1;

-- ---------------------------------------------------------------------
-- 4. Data Integrity & Logic Audit (AC 4)
-- These queries act as automated "exception reports" to find data entry errors or process violations.
-- ---------------------------------------------------------------------
-- Orphaned Shipments (Shipped without Quality Inspection):
SELECT l.lot_code, l.production_date, sr.ship_date, sr.destination_state
FROM lots l
JOIN shipping_records sr ON l.id = sr.lot_id
LEFT JOIN quality_inspection_records qr ON l.id = qr.lot_id
WHERE qr.id IS NULL;

-- Date Logic Errors (Ship Date before Production Date):
SELECT l.lot_code, l.production_date, sr.ship_date, 
       (sr.ship_date - l.production_date) AS day_variance
FROM lots l
JOIN shipping_records sr ON l.id = sr.lot_id
WHERE sr.ship_date < l.production_date;

-- ---------------------------------------------------------------------
-- 5. Source Health Monitor (AC 4)
-- To ensure the "Status Dashboard" is accurate, this query checks the freshness of the ingested spreadsheets.
-- ---------------------------------------------------------------------
SELECT 
    source_name, 
    last_updated_timestamp, 
    refresh_status,
    CASE 
        WHEN last_updated_timestamp < NOW() - INTERVAL '24 hours' THEN 'Stale'
        ELSE 'Current'
    END AS freshness_label
FROM data_source_metadatas;
