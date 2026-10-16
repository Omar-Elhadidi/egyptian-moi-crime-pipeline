# Egyptian Ministry of Interior (MOI) Crime News Intelligence Pipeline
## Requirements Gathering & System Specification (Milestone 3)

**Digital Egypt Pioneers Initiative (DEPI)**  
**Track:** Microsoft Data Engineer  
**Training Partner:** Skills Dynamix  
**Group Code:** ALX5_AIS5_S5  
**Round:** Round 5  
**Project Title:** Egyptian Ministry of Interior (MOI) Crime News Intelligence Pipeline & Analytics Platform  
**Repository:** [nhahub/NHA-5-079](https://github.com/nhahub/NHA-5-079)  
**Supervisor / Lecturer:** Eng. Ahmed Azab  
**Submission Date:** 16 October 2026  

---

## 1. Stakeholder Analysis

To ensure the platform delivers measurable value, we identified four primary stakeholder groups and mapped their specific requirements, expectations, and technical interactions with the system:

| Stakeholder Group | Primary Needs & Objectives | Interaction with System | Success Criteria |
|---|---|---|---|
| **Public Safety & Crime Analysts** | Timely, clean, and categorized crime incident data to detect emerging criminal patterns and seasonal surges across Egypt. | Consumes interactive filters, temporal aggregations, and spatial heatmaps on the Streamlit dashboard; exports filtered subsets. | Immediate access to historical and daily normalized records with zero manual spreadsheet cleanup. |
| **Law Enforcement / Policy Planners** | High-level regional risk distributions to evaluate security resource allocation and assess law enforcement campaigns by governorate. | Reviews executive summary metrics, geographic density heatmaps, and crime category distribution breakdowns. | Clear, high-level intelligence indicating high-density incident corridors and recurring crime categories. |
| **Data Platform Engineers & DevOps** | An automated, idempotent, resilient batch ingestion pipeline that requires minimal manual intervention and self-heals from transient failures. | Operates and monitors the Apache Airflow DAG, reviews pipeline logs, inspects data warehouse schemas, and manages Docker/Codespaces containers. | 100% idempotent batch loads, zero manual retries, automated logging, and zero duplicate rows on rerun. |
| **DEPI Academic Evaluators & Supervisors (Eng. Ahmed Azab)** | Demonstration of rigorous data engineering practices, architectural design patterns, dimensional modeling, automated testing, and code quality. | Evaluates GitHub repository, commits, Star Schema DDL, Pytest quality gates, Airflow DAG code, and technical documentation. | Production-grade code structure, clear separation of concerns, high test coverage, and adherence to DEPI rubric. |

---

## 2. User Stories & Use Cases

### 2.1 User Stories

- **US-01 (Spatial Incident Analysis):**  
  *As a* public safety researcher,  
  *I want to* filter reported crimes by Egyptian governorate on an interactive map,  
  *So that* I can visually identify geographical crime clusters and high-incident areas without writing raw SQL queries.

- **US-02 (Temporal Trend Tracking):**  
  *As a* security policy analyst,  
  *I want to* analyze monthly and seasonal crime volumes across specific crime categories (e.g., drug trafficking, theft, weapons offenses),  
  *So that* I can determine whether targeted enforcement campaigns have produced measurable drops in specific incident types.

- **US-03 (Automated Pipeline Execution & Idempotency):**  
  *As a* data platform engineer,  
  *I want* scheduled daily ingestion runs to automatically skip previously loaded articles,  
  *So that* rerunning the pipeline or backfilling historical data never produces duplicate records or corrupts analytical aggregations.

- **US-04 (Automated Quality Gate & Data Defense):**  
  *As a* quality assurance engineer,  
  *I want* the pipeline to automatically validate referential integrity and schema invariants before publishing data to the reporting layer,  
  *So that* downstream analytics dashboards never serve corrupt, orphaned, or truncated data to end users.

---

### 2.2 System Use Cases

#### Use Case UC-01: End-to-End Automated Batch Pipeline Execution
- **Primary Actor:** Apache Airflow Scheduler (System Actor)
- **Preconditions:** MOI news portal is accessible; PostgreSQL warehouse service is online.
- **Main Flow:**
  1. Airflow triggers `moi_crime_pipeline` DAG on a daily schedule (`@daily`).
  2. `extract_bronze` task scrapes new articles from the MOI portal and appends raw payloads to the Bronze JSON store with scrape timestamps.
  3. `transform_silver` task normalizes Arabic text, extracts entities (governorate, crime category, dates, metrics), geocodes locations, and updates `data/silver_crime_news.parquet`.
  4. `load_gold` task executes bulk upserts (`execute_values` with `ON CONFLICT DO NOTHING`) into PostgreSQL Star Schema dimension and fact tables.
  5. `quality_gate` task executes `pytest tests/test_warehouse.py`.
- **Postconditions:** Data warehouse is incrementally updated; 100% of data quality tests pass; pipeline execution logs are stored.
- **Alternative Flow (Quality Failure):** If an invariant fails (e.g., an orphan foreign key is detected), the DAG immediately terminates with failure, logs the assertion error, and halts downstream visualization refresh.

#### Use Case UC-02: Interactive Crime Analytics & Heatmap Visualization
- **Primary Actor:** Crime Analyst / Researcher
- **Preconditions:** Streamlit service is running and connected to the processed data layer.
- **Main Flow:**
  1. User navigates to the Streamlit web application.
  2. User selects filter criteria from the sidebar: Date Range, Governorate (e.g., Cairo, Alexandria, Giza), and Crime Category.
  3. System renders an interactive PyDeck density heatmap over an Egyptian map centered on the filtered incident coordinates.
  4. System renders interactive Plotly charts showing incident frequency over time and distribution across crime categories.
  5. User explores specific incidents and inspects summary statistics (Total Incidents, Total Suspects Apprehended, Seizure Counts).

---

## 3. Functional Requirements (FR)

| ID | Requirement Category | Detailed Description | Verification Method |
|---|---|---|---|
| **FR-01** | **Bronze Data Ingestion** | The system shall scrape unstructured crime news articles from official MOI channels, extracting article title, full text, publication date, and canonical URL. Raw payloads must be preserved in JSON format with metadata. | Inspection of `src/extract_crime_news.py` and raw JSON artifacts. |
| **FR-02** | **Arabic Text Normalization** | The system shall normalize Arabic characters (unifying variants of Alef `أ/إ/آ` to `ا`, Taa Marbuta `ة` to `ه`), strip extraneous whitespace and HTML tags, and standardize textual formatting. | Unit tests on Arabic text normalization functions in `src/transform_silver.py`. |
| **FR-03** | **Entity & Metric Extraction** | The system shall parse governorate names, crime classifications, incident dates, and numerical metrics (number of suspects, seized goods flag) from the narrative text using standardized pattern rules. | Verification of extracted fields in `data/silver_crime_news.parquet`. |
| **FR-04** | **Geocoding & Spatial Mapping** | The system shall resolve parsed Egyptian governorates and cities to standard geographic coordinates (latitude and longitude) bounded within the geographical borders of Egypt ($22^\circ\text{N} - 32^\circ\text{N}$, $24^\circ\text{E} - 37^\circ\text{E}$). | Pytest coordinate boundary invariant check. |
| **FR-05** | **Silver Parquet Serialization** | The system shall serialize the harmonized dataset into compressed Apache Parquet format, ensuring schema enforcement, column pruning capabilities, and fast read times. | Inspection of `data/silver_crime_news.parquet` metadata and read benchmarks. |
| **FR-06** | **Star Schema DDL Management** | The system shall establish and maintain a Kimball Star Schema in PostgreSQL consisting of four dimension tables (`dim_date`, `dim_crime_type`, `dim_location`, `dim_source`) and one central fact table (`fact_crime_incident`). | Execution of `sql/gold_schema.sql` against PostgreSQL. |
| **FR-07** | **Batch Loading & Idempotency** | The system shall bulk load Silver records into the Gold data warehouse using batched inserts (`execute_values`), enforcing idempotency through `ON CONFLICT (news_id) DO NOTHING`. | Rerunning `src/load_gold_warehouse.py` twice and verifying zero row count inflation. |
| **FR-08** | **Automated Data Quality Gate** | The system shall execute automated Pytest assertions verifying: volume threshold ($\ge 4,700$ records), zero orphan foreign keys, metric bounds, natural key uniqueness, and schema structural sanity. | Automated execution of `tests/test_warehouse.py` (5/5 tests passing). |
| **FR-09** | **Airflow DAG Orchestration** | The system shall automate the end-to-end pipeline via an Apache Airflow DAG (`dags/moi_crime_dag.py`) with configurable retry policies (`retries=2`, `retry_delay=5m`), task dependencies, and scheduled execution. | Airflow DAG integrity parse check and execution logs. |
| **FR-10** | **Geospatial & Trend Dashboard** | The system shall provide an interactive Streamlit application displaying geospatial incident heatmaps on an Egyptian base map, monthly volume trends, and multi-variable filtering. | Manual and functional verification of `app.py`. |

---

## 4. Non-Functional Requirements (NFR)

| ID | Quality Attribute | Specification / Acceptance Criteria |
|---|---|---|
| **NFR-01** | **Performance & Latency** | The Silver transformation of 4,700+ articles must complete in under 5 seconds. The Gold warehouse batch load must complete in under 5 seconds. The Streamlit dashboard must render filtered queries in under 2 seconds. |
| **NFR-02** | **Idempotency & Consistency** | Any pipeline task or the entire DAG can be executed multiple times over the same dataset without introducing duplicate records, orphan keys, or state drift. |
| **NFR-03** | **Data Integrity** | 100% referential integrity between `fact_crime_incident` and dimension tables. Fact foreign keys must strictly reference valid primary keys in dimensions (`ON DELETE RESTRICT`). |
| **NFR-04** | **Security & Credential Isolation** | Zero database passwords, access tokens, or hostnames shall be hardcoded in version-controlled scripts. All secrets must be loaded dynamically from an untracked `.env` file via `python-dotenv`. |
| **NFR-05** | **Portability & Containerization** | The system must run identically in cloud environments (GitHub Codespaces, Ubuntu Linux) and local environments without modifying source code paths. |
| **NFR-06** | **Maintainability & Modularity** | Codebase must adhere to modular enterprise engineering standards (`src/`, `data/`, `sql/`, `tests/`, `dags/`) with comprehensive type hints, function docstrings, and clean Git commit histories. |

---

## 5. Data Dictionary & Relational Specifications

### 5.1 Dimension Tables

#### `dim_date`
Represents the temporal hierarchy for analytical aggregation.
- `date_key` (INT, PK): Surrogate primary key in `YYYYMMDD` format.
- `full_date` (DATE, UNIQUE, NOT NULL): Calendar date.
- `year` (INT, NOT NULL): 4-digit calendar year.
- `month` (INT, NOT NULL): Month number (1–12).
- `month_name` (VARCHAR(20), NOT NULL): English month name (e.g., January).
- `day` (INT, NOT NULL): Day of month (1–31).
- `day_of_week` (VARCHAR(20), NOT NULL): Day name (e.g., Monday).
- `quarter` (INT, NOT NULL): Calendar quarter (1–4).
- `is_weekend` (BOOLEAN, NOT NULL): True if Friday/Saturday (Egypt weekend).

#### `dim_crime_type`
Standardized crime categorization hierarchy.
- `crime_type_key` (SERIAL, PK): Surrogate primary key.
- `crime_category` (VARCHAR(100), UNIQUE, NOT NULL): Primary standardized crime category (e.g., Drug Offenses, Theft & Robbery, Illegal Firearms, Commercial Fraud, Cybercrime, Public Order).
- `severity_level` (VARCHAR(20)): Low / Medium / High / Critical.
- `description` (TEXT): Analytical description and legal classification scope.

#### `dim_location`
Geographic hierarchy for Egyptian administrative divisions.
- `location_key` (SERIAL, PK): Surrogate primary key.
- `governorate` (VARCHAR(100), NOT NULL): Standardized Egyptian governorate name (e.g., Cairo, Alexandria, Giza, Dakahlia, Sharkia).
- `city` (VARCHAR(100)): Specific municipality or district if identified.
- `latitude` (NUMERIC(9,6)): Centroid latitude coordinate.
- `longitude` (NUMERIC(9,6)): Centroid longitude coordinate.
- `region` (VARCHAR(50)): Geographic region (e.g., Greater Cairo, Delta, Canal, Upper Egypt, Frontier).

#### `dim_source`
Lineage tracking of official public release channels.
- `source_key` (SERIAL, PK): Surrogate primary key.
- `source_name` (VARCHAR(100), NOT NULL): Channel name (e.g., MOI Official Portal, MOI Facebook Media Office).
- `source_url_domain` (VARCHAR(255)): Domain or base channel URL.
- `reliability_tier` (VARCHAR(20)): Official Government / Verified Press.

---

### 5.2 Fact Table

#### `fact_crime_incident`
The central grain of the warehouse: one row per verified published crime incident.
- `incident_key` (BIGSERIAL, PK): Surrogate primary key.
- `news_id` (VARCHAR(100), UNIQUE, NOT NULL): Natural unique business key from source publication.
- `date_key` (INT, NOT NULL, FK $\rightarrow$ `dim_date.date_key`): Incident publication date.
- `crime_type_key` (INT, NOT NULL, FK $\rightarrow$ `dim_crime_type.crime_type_key`): Classification.
- `location_key` (INT, NOT NULL, FK $\rightarrow$ `dim_location.location_key`): Geographic location.
- `source_key` (INT, NOT NULL, FK $\rightarrow$ `dim_source.source_key`): Media source.
- `suspects_count` (INT, DEFAULT 1): Number of apprehended suspects reported.
- `seizure_flag` (BOOLEAN, DEFAULT FALSE): Indicates whether physical contraband, narcotics, or weapons were seized.
- `title` (TEXT, NOT NULL): Original news release headline.
- `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT CURRENT_TIMESTAMP): Warehouse ingestion timestamp.
