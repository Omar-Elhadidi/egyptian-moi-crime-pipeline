import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")


def run_query(sql):
    conn = None
    try:
        with psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "moi_crime_dw"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "1021"),
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                return cursor.fetchone()[0]
            
    finally:
        if conn is not None:
            conn.close()


def test_warehouse_row_count():
    """Test 1: Completeness - Verifies fact_crime loaded at least 4,700 records."""
    count = run_query("SELECT COUNT(*) FROM fact_crime;")
    assert count >= 4700, f"Expected >= 4700 facts, but found {count}"


def test_zero_orphaned_foreign_keys():
    """Test 2: Referential Integrity - Verifies all facts link to existing dimensions."""
    orphan_locations = run_query("""
        SELECT COUNT(*) FROM fact_crime f
        LEFT JOIN dim_location l ON f.location_id = l.location_id
        WHERE l.location_id IS NULL;
    """)

    orphan_dates = run_query("""
        SELECT COUNT(*) FROM fact_crime f
        LEFT JOIN dim_date d ON f.date_id = d.date_id
        WHERE d.date_id IS NULL;
    """)

    orphan_types = run_query("""
        SELECT COUNT(*) FROM fact_crime f
        LEFT JOIN dim_crime_type c ON f.crime_type_id = c.crime_type_id
        WHERE c.crime_type_id IS NULL;
    """)

    total_orphans = orphan_locations + orphan_dates + orphan_types
    assert total_orphans == 0, f"Found {total_orphans} orphaned records in fact_crime!"


def test_metric_ranges():
    """Test 3: Domain Rules - Verifies metrics obey realistic boundaries."""
    invalid_counts = run_query("""
        SELECT COUNT(*) FROM fact_crime
        WHERE suspects_count < 1 OR incident_count < 1;
    """)

    invalid_severities = run_query("""
        SELECT COUNT(*) FROM dim_crime_type
        WHERE severity_level NOT BETWEEN 1 AND 5;
    """)

    assert invalid_counts == 0, f"Found {invalid_counts} facts with non-positive counts"
    assert invalid_severities == 0, f"Found {invalid_severities} types with invalid severity"

def test_no_duplicate_articles():
    """Test 5: Uniqueness - Verifies no news article is ingested more than once."""
    duplicate_count = run_query("""
        SELECT COUNT(news_id) - COUNT(DISTINCT news_id) 
        FROM fact_crime;
    """)
    assert duplicate_count == 0, f"Found {duplicate_count} duplicate articles in fact_crime!"


def test_dimension_completeness():
    """Test 4: Schema Sanity - Verifies critical descriptive attributes are not NULL."""
    null_govs = run_query("SELECT COUNT(*) FROM dim_location WHERE governorate_en IS NULL;")
    null_cats = run_query("SELECT COUNT(*) FROM dim_crime_type WHERE category_en IS NULL;")

    assert null_govs == 0, f"Found {null_govs} locations with NULL governorate"
    assert null_cats == 0, f"Found {null_cats} categories with NULL category name"