-- =============================================================================
-- Database Schema: MOI Crime News Data Warehouse (Star Schema)
-- Project: MOI Crime News Ingestion & Analytics Pipeline (work-flow-main)
-- Target RDBMS: PostgreSQL 15+
-- Architecture: Medallion Architecture (Gold Analytics Warehouse Layer)
-- =============================================================================

-- Drop tables if re-deploying (cascading foreign keys)
DROP TABLE IF EXISTS fact_crime CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;
DROP TABLE IF EXISTS dim_location CASCADE;
DROP TABLE IF EXISTS dim_crime_type CASCADE;

-- =============================================================================
-- 1. DIM_DATE (Date Dimension)
-- Surrogate Key: YYYYMMDD integer format (e.g. 20260927) for rapid integer joins
-- =============================================================================
CREATE TABLE dim_date (
    date_id INT PRIMARY KEY,                       -- Format: YYYYMMDD (e.g., 20260927)
    calendar_date DATE NOT NULL UNIQUE,
    year SMALLINT NOT NULL,
    quarter SMALLINT NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    month SMALLINT NOT NULL CHECK (month BETWEEN 1 AND 12),
    month_name VARCHAR(20) NOT NULL,              -- e.g., 'September'
    day_of_month SMALLINT NOT NULL CHECK (day_of_month BETWEEN 1 AND 31),
    day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 1 AND 7), -- 1=Sunday, 7=Saturday
    day_name VARCHAR(20) NOT NULL,                -- e.g., 'Sunday'
    week_of_year SMALLINT NOT NULL,
    is_weekend BOOLEAN NOT NULL                   -- True for Friday/Saturday in Egypt
);

-- =============================================================================
-- 2. DIM_LOCATION (Egyptian Governorates & Administrative Regions)
-- =============================================================================
CREATE TABLE dim_location (
    location_id SERIAL PRIMARY KEY,
    governorate_ar VARCHAR(50) NOT NULL UNIQUE,
    governorate_en VARCHAR(50) NOT NULL UNIQUE,
    region VARCHAR(50) NOT NULL                   -- Greater Cairo, Delta, Canal, Upper Egypt, Frontier
);

-- =============================================================================
-- 3. DIM_CRIME_TYPE (Standardized MOI Crime Taxonomy)
-- =============================================================================
CREATE TABLE dim_crime_type (
    crime_type_id SERIAL PRIMARY KEY,
    category_ar VARCHAR(100) NOT NULL UNIQUE,
    category_en VARCHAR(100) NOT NULL UNIQUE,
    severity_level SMALLINT NOT NULL CHECK (severity_level BETWEEN 1 AND 5) 
    -- 1: Public Order / Minor Violation
    -- 2: Theft / Property
    -- 3: Economic / Fraud / Counterfeit
    -- 4: Narcotics / Illicit Weapons
    -- 5: Homicide / Armed Gangs / Terrorism
);

-- =============================================================================
-- 4. FACT_CRIME (Central Fact Table)
-- Grain: One record per law enforcement incident reported by the MOI
-- =============================================================================
CREATE TABLE fact_crime (
    crime_fact_id BIGSERIAL PRIMARY KEY,
    news_id UUID NOT NULL UNIQUE,                 -- MOI unique identifier (Natural/Business Key)
    date_id INT NOT NULL REFERENCES dim_date(date_id),
    location_id INT NOT NULL REFERENCES dim_location(location_id),
    crime_type_id INT NOT NULL REFERENCES dim_crime_type(crime_type_id),
    
    -- Content & Metadata
    title TEXT NOT NULL,
    full_details TEXT NOT NULL,
    source_url TEXT,
    image_url TEXT,
    
    -- Measures & Metrics
    incident_count INT NOT NULL DEFAULT 1,
    suspects_count INT NOT NULL DEFAULT 1,
    weapons_count INT NOT NULL DEFAULT 0,
    is_campaign BOOLEAN NOT NULL DEFAULT FALSE,
    published_timestamp TIMESTAMP NOT NULL,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- PERFORMANCE INDEXES (Star Schema Optimization)
-- =============================================================================
CREATE INDEX idx_fact_crime_date ON fact_crime(date_id);
CREATE INDEX idx_fact_crime_location ON fact_crime(location_id);
CREATE INDEX idx_fact_crime_type ON fact_crime(crime_type_id);
CREATE INDEX idx_fact_crime_news_id ON fact_crime(news_id);
CREATE INDEX idx_fact_crime_published_ts ON fact_crime(published_timestamp);

-- =============================================================================
-- SEED DATA: Unknown / Fallback Record (ID 0)
-- Standard dimensional modeling practice for handling unparsed / missing data
-- =============================================================================
INSERT INTO dim_location (location_id, governorate_ar, governorate_en, region)
OVERRIDING SYSTEM VALUE
VALUES (0, 'غير محدد', 'Unknown', 'Unknown');

INSERT INTO dim_crime_type (crime_type_id, category_ar, category_en, severity_level)
OVERRIDING SYSTEM VALUE
VALUES (0, 'أخرى / غير مصنف', 'Other / Unclassified', 1);

-- =============================================================================
-- SEED DATA: 27 Egyptian Governorates Reference Data
-- =============================================================================
INSERT INTO dim_location (governorate_ar, governorate_en, region) VALUES
-- Greater Cairo
('القاهرة', 'Cairo', 'Greater Cairo'),
('الجيزة', 'Giza', 'Greater Cairo'),
('القليوبية', 'Qalyubia', 'Greater Cairo'),
-- Alexandria & Delta
('الإسكندرية', 'Alexandria', 'Alexandria'),
('البحيرة', 'Beheira', 'Delta'),
('كفر الشيخ', 'Kafr El Sheikh', 'Delta'),
('الغربية', 'Gharbia', 'Delta'),
('المنوفية', 'Monufia', 'Delta'),
('الدقهلية', 'Dakahlia', 'Delta'),
('الشرقية', 'Sharqia', 'Delta'),
('دمياط', 'Damietta', 'Delta'),
-- Canal Zone
('بورسعيد', 'Port Said', 'Canal'),
('الإسماعيلية', 'Ismailia', 'Canal'),
('السويس', 'Suez', 'Canal'),
-- North Upper Egypt
('الفيوم', 'Faiyum', 'Upper Egypt'),
('بني سويف', 'Beni Suef', 'Upper Egypt'),
('المنيا', 'Minya', 'Upper Egypt'),
-- South Upper Egypt
('أسيوط', 'Asyut', 'Upper Egypt'),
('سوهاج', 'Sohag', 'Upper Egypt'),
('قنا', 'Qena', 'Upper Egypt'),
('الأقصر', 'Luxor', 'Upper Egypt'),
('أسوان', 'Aswan', 'Upper Egypt'),
-- Frontier & Coastal
('البحر الأحمر', 'Red Sea', 'Frontier'),
('الوادي الجديد', 'New Valley', 'Frontier'),
('مطروح', 'Matrouh', 'Frontier'),
('شمال سيناء', 'North Sinai', 'Frontier'),
('جنوب سيناء', 'South Sinai', 'Frontier');

-- =============================================================================
-- SEED DATA: Core Egyptian Crime Taxonomy (Standardized Categories)
-- =============================================================================
INSERT INTO dim_crime_type (category_ar, category_en, severity_level) VALUES
('بلطجة وفرض سيطرة', 'Thuggery & Extortion', 5),
('تجارة المواد المخدرة', 'Narcotics Trafficking', 4),
('حيازة أسلحة نارية وذخائر', 'Illegal Firearm Possession', 4),
('سرقة بالإكراه وتشكيل عصابي', 'Armed Robbery & Gang Activity', 4),
('سرقة مساكن ومتاجر', 'Burglary & Larceny', 2),
('نصب واحتيال وتوظيف أموال', 'Fraud & Financial Scams', 3),
('جرائم إلكترونية وابتزاز', 'Cybercrime & Blackmail', 3),
('غسيل أموال وكسب غير مشروع', 'Money Laundering', 4),
('شروع في قتل وقتل عمد', 'Attempted Murder & Homicide', 5),
('تهريب وجرائم جمركية', 'Smuggling & Customs Evasion', 3),
('تعديات على الأراضي ومباني مخالفة', 'Land Encroachment & Illegal Building', 2),
('مخالفات تموينية واحتكار سلع', 'Price Gouging & Food Supply Violations', 2);

-- =============================================================================
-- SEED DATA: Automated Date Dimension Generation (2018 - 2030)
-- =============================================================================
INSERT INTO dim_date (
    date_id, calendar_date, year, quarter, month, month_name, 
    day_of_month, day_of_week, day_name, week_of_year, is_weekend
) VALUES (
    0, '1900-01-01', 1900, 1, 1, 'Unknown', 1, 1, 'Unknown', 1, FALSE
) ON CONFLICT (date_id) DO NOTHING;

INSERT INTO dim_date (
    date_id, calendar_date, year, quarter, month, month_name,
    day_of_month, day_of_week, day_name, week_of_year, is_weekend
)
SELECT
    TO_CHAR(datum, 'YYYYMMDD')::INT AS date_id,
    datum::DATE AS calendar_date,
    EXTRACT(YEAR FROM datum)::SMALLINT AS year,
    EXTRACT(QUARTER FROM datum)::SMALLINT AS quarter,
    EXTRACT(MONTH FROM datum)::SMALLINT AS month,
    TRIM(TO_CHAR(datum, 'Month')) AS month_name,
    EXTRACT(DAY FROM datum)::SMALLINT AS day_of_month,
    EXTRACT(ISODOW FROM datum)::SMALLINT AS day_of_week,
    TRIM(TO_CHAR(datum, 'Day')) AS day_name,
    EXTRACT(WEEK FROM datum)::SMALLINT AS week_of_year,
    CASE WHEN EXTRACT(ISODOW FROM datum) IN (5, 6) THEN TRUE ELSE FALSE END AS is_weekend
FROM generate_series(
    '2018-01-01'::DATE,
    '2030-12-31'::DATE,
    '1 day'::INTERVAL
) AS datum
ON CONFLICT (date_id) DO NOTHING;
