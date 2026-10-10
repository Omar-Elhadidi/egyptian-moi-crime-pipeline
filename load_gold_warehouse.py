import os
import sys
import time
from pathlib import Path
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from  dotenv import load_dotenv
load_dotenv() 


# Ensure UTF-8 output in Windows PowerShell/cmd terminals
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_silver_to_gold(parquet_path=None):
    """
    Bulk loads records from Silver Parquet into PostgreSQL Gold Warehouse (fact_crime).
    Guarantees idempotency via ON CONFLICT (news_id) DO NOTHING.
    """
    base_dir = Path(__file__).parent

    if parquet_path is None:
        parquet_path = base_dir / "silver_crime_news.parquet"
    else:
        parquet_path = Path(parquet_path)

    if not parquet_path.exists():
        print(f"❌ Error: Silver Parquet file not found at {parquet_path}")
        sys.exit(1)

    print("=" * 70)
    print("🚀 STARTING GOLD WAREHOUSE LOADER")
    print(f"📦 Source (Silver): {parquet_path.name}")
    print(f"🎯 Target Database: {os.getenv('DB_NAME', 'moi_crime_dw')}")
    print("=" * 70)

    start_time = time.time()

    # 1. Read Silver Parquet
    df = pd.read_parquet(parquet_path)
    total_silver_rows = len(df)
    print(f"Loaded {total_silver_rows:,} records from Silver Parquet.")

    # Convert DataFrame rows into a list of tuples for psycopg2
    records_to_insert = [
        (
            row["news_id"],
            int(row["date_id"]),
            int(row["location_id"]),
            int(row["crime_type_id"]),
            row["title"],
            row["full_details"],
            row["source_url"],
            row["image_url"],
            int(row["incident_count"]),
            int(row["suspects_count"]),
            int(row["weapons_count"]),
            bool(row["is_campaign"]),
            row["published_timestamp"],
            row["ingested_at"]
        )
        for _, row in df.iterrows()
    ]

    # 2. Connect to PostgreSQL
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "moi_crime_dw")
    db_user = os.getenv("DB_USER", "postgres")
    db_pass = os.getenv("DB_PASSWORD", "")

    conn = None

    try:
        with psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_pass
        ) as conn:
            
            with conn.cursor() as cursor:
                print(f" Connected to PostgreSQL: {db_user}@{db_host}:{db_port}/{db_name}")

                # 3. Fast Bulk Insert using execute_values
                insert_query = """
                INSERT INTO fact_crime (
                    news_id, date_id, location_id, crime_type_id,
                    title, full_details, source_url, image_url,
                    incident_count, suspects_count, weapons_count, is_campaign,
                    published_timestamp, ingested_at
                ) VALUES %s
                ON CONFLICT (news_id) DO NOTHING;
                """

                print(f"⏳ Bulk inserting {len(records_to_insert):,} rows into fact_crime...")
                execute_values(cursor, insert_query, records_to_insert, page_size=1000)

                # 4. Warehouse Verification Queries
                cursor.execute("SELECT COUNT(*) FROM fact_crime;")
                total_in_warehouse = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM fact_crime WHERE location_id > 0;")
                with_location = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM fact_crime WHERE crime_type_id > 0;")
                with_crime = cursor.fetchone()[0]

                cursor.execute("SELECT SUM(suspects_count), SUM(weapons_count), SUM(CASE WHEN is_campaign THEN 1 ELSE 0 END) FROM fact_crime;")
                total_suspects, total_weapons, total_campaigns = cursor.fetchone()

                duration = time.time() - start_time

                print("\n" + "=" * 70)
                print("🎉 GOLD WAREHOUSE LOAD COMPLETE!")
                print(f"📊 Total Rows in fact_crime   : {total_in_warehouse:,}")
                print(f"📍 Mapped to Known Location   : {with_location:,} ({(with_location/total_in_warehouse)*100:.1f}%)")
                print(f"🏷️ Mapped to Crime Category   : {with_crime:,} ({(with_crime/total_in_warehouse)*100:.1f}%)")
                print(f"👥 Total Suspects Tracked     : {int(total_suspects):,}")
                print(f"🔫 Total Weapons Tracked      : {int(total_weapons):,}")
                print(f"🚔 Total Security Campaigns   : {int(total_campaigns):,}")
                print(f"⏱️ Load Duration              : {duration:.2f} seconds")
                print("=" * 70)

    except Exception as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    load_silver_to_gold()
