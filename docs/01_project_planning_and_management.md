# Egyptian Ministry of Interior (MOI) Crime News Intelligence Pipeline
## Project Planning & Management Document (Milestone 1)

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

## 1. Project Proposal (Standard DEPI Template)

### Project Name
**Egyptian Ministry of Interior (MOI) Crime News Intelligence Pipeline & Analytics Platform**

### Objective
To engineer an automated, production-grade batch data pipeline that extracts unstructured crime press releases from official Egyptian Ministry of Interior (MOI) public communications, cleans and normalizes Arabic incident narratives across a Medallion Architecture (Bronze $\rightarrow$ Silver $\rightarrow$ Gold), populates an idempotent PostgreSQL Star Schema data warehouse, validates referential integrity and data constraints via automated test suites, and exposes spatial-temporal crime analytics through an interactive Streamlit dashboard.

### Description
Public security and crime reports in Egypt are primarily published as unstructured text releases through the official Ministry of Interior portal and media statements. Due to the absence of centralized, structured open data APIs, security researchers, public policy analysts, and journalists face severe barriers in analyzing national crime trends, regional distribution, and seasonal crime patterns.

This project bridges that gap by establishing an end-to-end data platform:
1. **Bronze Layer (Raw Ingestion):** Automated scrapers capture raw press releases, preserving metadata, raw HTML text, publication dates, and source URLs in raw JSON format.
2. **Silver Layer (Transformation & Normalization):** High-throughput text-processing engines clean Arabic text, normalize governorate and city names, categorize crime classifications, extract metrics (suspect counts, seizures), and persist deduplicated records in compressed Apache Parquet format (4,709+ verified historical incidents).
3. **Gold Layer (Analytical Warehouse):** A Kimball Star Schema in PostgreSQL featuring four dimension tables (`dim_date`, `dim_crime_type`, `dim_location`, `dim_source`) and a central fact table (`fact_crime_incident`) populated via bulk upserts (`execute_values` with `ON CONFLICT DO NOTHING`).
4. **Data Quality Gate:** An automated `pytest` suite enforcing 5 critical invariants (zero foreign key orphans, volume thresholds, coordinate boundaries, natural key uniqueness, schema integrity).
5. **Orchestration:** Apache Airflow DAG managing automated daily pipeline runs, error handling, retries, and dependent execution.
6. **Analytics Serving:** An interactive Streamlit dashboard displaying geographic incident heatmaps across Egyptian governorates, temporal distribution, and categorical security breakdowns.

### Tools & Design
- **Architecture & Design:** Medallion Architecture (Bronze / Silver / Gold), Kimball Dimensional Modeling (Star Schema), Test-Driven Data Engineering (Automated Quality Gates), DAG-based Pipeline Orchestration.
- **Tools:** Python 3.11+, PostgreSQL 16, Apache Airflow 2.x, Pytest, Streamlit, PyDeck, Plotly, Git, GitHub, Docker / GitHub Codespaces.

### Technologies to Use
- **Data Ingestion & Scraping:** Python `requests`, `BeautifulSoup4`
- **Data Transformation & Storage:** Python, `pandas`, `pyarrow` (Apache Parquet)
- **Data Warehousing & Modeling:** PostgreSQL 16, `psycopg2-binary`, `SQLAlchemy`, SQL DDL
- **Data Quality & Testing:** `pytest`
- **Workflow Orchestration:** Apache Airflow (`BashOperator`, DAG scheduling)
- **Interactive Visualization:** Streamlit, `pydeck` (GIS Heatmap), `plotly`
- **Environment & Version Control:** Git, GitHub, `.env` secret management, Docker / GitHub Codespaces

---

### Team Members & Responsibilities

| # | Name | LMS / GitHub Email | Role / Responsibility |
|---|---|---|---|
| 1 | **Ahmed Ali Ahmed Ali** | `ahmed.a.ali.tech@gmail.com` | **Project Team Leader** / NLP & LLM Extraction Experimentation |
| 2 | **Omar Tamer Mostafa Elhadidi** | `omar.t.elhadidi@gmail.com` | **Data Engineering Lead** / Pipeline Architecture, Medallion Engine (Bronze, Silver, Gold), PostgreSQL Star Schema DDL, Automated Pytest Suite, Airflow DAG Orchestration |
| 3 | **Mahmoud Ibrahim Abdul Qader Ibrahim** | `mahmoud.ibrahim.eg1@gmail.com` | **Data Modeling & Architecture** / Star Schema Design & Dimensional Modeling Review |
| 4 | **Sondos Ahmed Mabrouk Habiba** | `sondosahmed5425@gmail.com` | *[Front-end Dashboard & Visualization / Data Exploration - To be confirmed by member]* |
| 5 | **Konoz Nashaat** | `konoznashaat123@gmail.com` | *[Data Verification, Quality Assurance & Documentation - To be confirmed by member]* |
| 6 | **Shahd Nezar Atef Hagag** | `shahdhagag.ss@gmail.com` | *[Reporting, Literature Review & User Acceptance - To be confirmed by member]* |

---

### Weekly Work Breakdown & Deliverables

#### Week 1: Project Scoping, Architecture & Repository Setup
- **Tasks Description:**
  - Define project problem statement, objectives, and scope.
  - Explore Egyptian MOI news sources and identify data structures.
  - Initialize the official GitHub repository (`nhahub/NHA-5-079`), establish branch protections, directory layouts, and environment variable standards.
  - Team Member Responsibility:
    - Architecture & Repository Initialization: Omar Elhadidi
    - Problem Formulation & Team Coordination: Ahmed Ali (Team Leader)
    - Schema Brainstorming: Mahmoud Ibrahim
    - Exploratory Data Gathering: *[Sondos Ahmed, Konoz Nashaat, Shahd Nezar]*
- **Deliverables:**
  - Initialized GitHub repository with `.gitignore`, `README.md`, and `.env.example`.
  - Project Proposal Document (Draft).
  - Raw sample data extracts.

#### Week 2: Ingestion & Silver Normalization (Medallion Layers 1 & 2)
- **Tasks Description:**
  - Build automated ingestion scraper for MOI news portal to capture historical and daily articles.
  - Implement Silver transformation module in Python: Arabic text cleaning, character normalization (Alef, Taa Marbuta), regex-based entity extraction (governorate, crime category, dates), coordinate geocoding, and deduplication.
  - Persist processed records into compressed Apache Parquet format.
  - Conduct preliminary LLM extraction tests on a pilot sample.
  - Team Member Responsibility:
    - Bronze & Silver Pipeline Engine (`extract_crime_news.py`, `transform_silver.py`): Omar Elhadidi
    - LLM Prompting & Sample Extraction (`extracted_news.json`): Ahmed Ali
    - Geocoding Verification & Reference Data Mapping: *[Sondos Ahmed, Konoz Nashaat, Shahd Nezar]*
- **Deliverables:**
  - `src/extract_crime_news.py` (Bronze Ingestion).
  - `src/transform_silver.py` (Silver Transformation).
  - `data/silver_crime_news.parquet` containing 4,709 cleaned and normalized records.
  - LLM extraction experimental evaluation.

#### Week 3: Data Warehousing, Idempotent Loading & Automated Testing
- **Tasks Description:**
  - Design and execute PostgreSQL Kimball Star Schema DDL (`dim_date`, `dim_crime_type`, `dim_location`, `dim_source`, `fact_crime_incident`).
  - Implement bulk warehouse loader (`src/load_gold_warehouse.py`) using `psycopg2.extras.execute_values` and `ON CONFLICT (news_id) DO NOTHING` for idempotent execution.
  - Build automated data quality test suite (`tests/test_warehouse.py`) running 5 invariant checks with `pytest`.
  - Team Member Responsibility:
    - Gold Loader & Pytest Quality Suite Implementation: Omar Elhadidi
    - Star Schema Specification & Relational Constraints: Mahmoud Ibrahim
    - Schema Documentation & Data Dictionary: *[Sondos Ahmed, Konoz Nashaat, Shahd Nezar]*
- **Deliverables:**
  - `sql/gold_schema.sql` (Production Star Schema DDL).
  - `src/load_gold_warehouse.py` (Production Gold Loader).
  - `tests/test_warehouse.py` (5 automated invariants passing in < 2.0s).
  - Fully populated PostgreSQL Data Warehouse.

#### Week 4: Airflow Orchestration, Dashboard Analytics & Milestone Delivery
- **Tasks Description:**
  - Develop Apache Airflow DAG (`dags/moi_crime_dag.py`) orchestrating Bronze Ingestion $\rightarrow$ Silver Transformation $\rightarrow$ Gold Loading $\rightarrow$ Pytest Quality Gate.
  - Configure DAG retry policies, execution intervals (`@daily`), and task dependency chains.
  - Finalize interactive Streamlit analytical application (`app.py`) featuring governorate heatmaps, temporal trends, and crime category distribution.
  - Compile Milestone 1–3 official DEPI documentation (Planning, Literature Review, Requirements).
  - Team Member Responsibility:
    - Airflow DAG Orchestration & Automation: Omar Elhadidi
    - Streamlit Dashboard Features & UI: *[Omar Elhadidi / Sondos Ahmed]*
    - Team Coordination & Deliverable Finalization: Ahmed Ali
    - Documentation Compilation: *[Konoz Nashaat, Shahd Nezar]*
- **Deliverables:**
  - `dags/moi_crime_dag.py` (Airflow Orchestration).
  - `app.py` (Streamlit Analytics Application).
  - Milestone Documentation (Project Planning, Literature Review, Requirements Gathering).

---

## 2. Project Plan & Milestones

### Project Timeline & Schedule

| Phase | Milestone | Start Date | Due Date | Status |
|---|---|---|---|---|
| Phase 1 | Project Planning & Proposal (Milestone 1) | 02 Oct 2026 | 16 Oct 2026 | Complete |
| Phase 1 | Literature Review (Milestone 2) | 09 Oct 2026 | 16 Oct 2026 | Complete |
| Phase 1 | Requirements Gathering (Milestone 3) | 09 Oct 2026 | 16 Oct 2026 | Complete |
| Phase 2 | System Analysis & Design (ERD, DFD, Architecture) | 16 Oct 2026 | 06 Nov 2026 | In Progress |
| Phase 3 | Core Implementation & Pipeline Execution | 16 Oct 2026 | 30 Nov 2026 | In Progress |
| Phase 4 | Final Presentation, Quality Reports & Delivery | 30 Nov 2026 | 04 Dec 2026 | Scheduled |

### Resource Allocation

- **Compute & Local Development:** Standard developer workstations (Windows/Linux) running Python 3.11+ and PostgreSQL 16.
- **Containerized Orchestration:** GitHub Codespaces (cloud Ubuntu 22.04 LTS environment with pre-installed Docker and 4-core compute) to eliminate local GPU/Hyper-V hardware conflicts.
- **Data Storage:** Local and cloud-hosted PostgreSQL database; compressed columnar Apache Parquet storage for intermediate analytical caching.
- **APIs & LLM Services:** Free-tier OpenAI / Groq / HuggingFace endpoints used selectively for AI benchmarking sample evaluation without incurring cloud infrastructure bills.

---

## 3. Task Assignment & RACI Matrix

- **R** = Responsible (Does the work)
- **A** = Accountable (Approves and owns final outcome)
- **C** = Consulted (Provides technical/functional input)
- **I** = Informed (Kept updated on progress)

| Project Component / Activity | Ahmed Ali (TL) | Omar Elhadidi | Mahmoud Ibrahim | Sondos Habiba | Konoz Nashaat | Shahd Hagag |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Project Management & Timeline | **A** | C | C | I | I | I |
| Architecture & Medallion Pipeline | I | **A / R** | C | I | I | I |
| Scraping & Bronze Ingestion | I | **A / R** | I | I | I | I |
| Silver Transformation & Geocoding | I | **A / R** | C | C | I | I |
| LLM Pilot Extraction Testing | **A / R** | C | I | I | I | I |
| Kimball Star Schema Design | I | R | **A / R** | I | I | I |
| Gold Warehouse Batch Loading | I | **A / R** | C | I | I | I |
| Automated Pytest Quality Gate | I | **A / R** | I | I | I | I |
| Airflow DAG Orchestration | I | **A / R** | I | I | I | I |
| Streamlit Dashboard Development | I | R | I | **R** | I | I |
| Documentation & Requirements | C | R | C | R | **R** | **R** |

---

## 4. Risk Assessment & Mitigation Plan

| # | Risk Description | Severity | Probability | Impact | Mitigation Strategy |
|---|---|:---:|:---:|:---:|---|
| **R1** | **Target Website Structure Change / Downtime** | High | Medium | Scraping breaks; pipeline fails to ingest new articles. | Store complete raw HTML and response payloads in the Bronze layer; implement robust exception handling and fallback selectors; log unparseable articles for manual review. |
| **R2** | **LLM Latency, Cost & Rate Limits** | High | High | Ingestion grinds to a halt; rate limits block processing of 4,700+ articles. | Adopt a hybrid engineering strategy: use high-throughput, deterministic regex/rule-based processing for primary ingestion (4,700+ records), and reserve LLM processing for a benchmark sample of 30–50 articles. |
| **R3** | **Data Quality Degradation / Orphan Foreign Keys** | Critical | Low | Corrupted reporting; fact records point to non-existent dimension keys. | Enforce database-level foreign key constraints (`ON DELETE RESTRICT`); embed an automated `pytest` quality gate into the Airflow DAG that halts execution if orphan records $> 0$. |
| **R4** | **Hardware / Driver Incompatibilities (Windows Hyper-V vs Docker)** | High | Medium | Inability to run Dockerized Airflow locally due to AMD/Intel virtualization driver conflicts. | Standardize containerized execution on GitHub Codespaces (cloud Linux environment with native Docker support), decoupling pipeline development from local laptop hardware. |
| **R5** | **Team Coordination & Task Bottlenecks** | Medium | Medium | Slower progress if members block on upstream components. | Maintain a clear separation of concerns: modular codebase with clean interfaces (`data/silver_crime_news.parquet` serves as a contract between data engineering and dashboard development). |

---

## 5. Key Performance Indicators (KPIs)

To evaluate the operational success, data integrity, and engineering quality of the platform, the following KPIs have been established:

| KPI Category | Metric | Target | Verification Method |
|---|---|---|---|
| **Throughput** | Bronze-to-Silver processing throughput | $\ge$ 1,000 articles / min | Benchmarked execution time of `transform_silver.py` |
| **Warehouse Loading** | Gold warehouse load speed (4,700+ records) | $\le$ 5.0 seconds | Timed batch execution with `execute_values` |
| **Idempotency** | Duplicate records produced on rerun | **0 records** | Validated via `ON CONFLICT (news_id) DO NOTHING` |
| **Data Quality** | Automated Test Suite Pass Rate | **100% (5/5 invariants)** | `pytest tests/test_warehouse.py` execution |
| **Referential Integrity**| Orphan foreign keys in Fact table | **0 orphans** | Automated SQL check in `test_zero_foreign_key_orphans` |
| **System Uptime** | Airflow DAG success rate | $\ge 99\%$ | Airflow task monitoring and automated retry logs |
| **Dashboard Latency** | Streamlit filter and heatmap render time | $\le 1.5$ seconds | Browser network/render inspection |
