import logging
from google.cloud import bigquery
from datetime import datetime

logger = logging.getLogger(__name__)

PROJECT_ID = "ledger-fcc1e"
DATASET_ID = "retail_payment_base"
TABLE_ID = "merchants_gmaps"


def get_bigquery_client():
    """Get authenticated BigQuery client."""
    return bigquery.Client(project=PROJECT_ID)


def create_table_if_not_exists():
    """Create BigQuery table if it doesn't exist."""
    client = get_bigquery_client()
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    schema = [
        bigquery.SchemaField("google_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("name", "STRING"),
        bigquery.SchemaField("address", "STRING"),
        bigquery.SchemaField("lat", "FLOAT64"),
        bigquery.SchemaField("lng", "FLOAT64"),
        bigquery.SchemaField("rating", "FLOAT64"),
        bigquery.SchemaField("review_count", "INTEGER"),
        bigquery.SchemaField("phone", "STRING"),
        bigquery.SchemaField("hours", "STRING"),
        bigquery.SchemaField("google_category", "STRING"),
        bigquery.SchemaField("status", "STRING"),
        bigquery.SchemaField("our_category", "STRING"),
        bigquery.SchemaField("vertical", "STRING"),
        bigquery.SchemaField("kecamatan_name", "STRING"),
        bigquery.SchemaField("kabupaten_name", "STRING"),
        bigquery.SchemaField("provinsi_name", "STRING"),
        bigquery.SchemaField("district_id", "STRING"),
        bigquery.SchemaField("scraped_at", "TIMESTAMP"),
    ]

    table = bigquery.Table(table_id, schema=schema)
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="scraped_at",
    )
    table.clustering_fields = ["kecamatan_name", "our_category"]

    try:
        client.get_table(table_id)
        logger.info(f"Table {table_id} already exists")
    except Exception:
        logger.info(f"Creating table {table_id}...")
        client.create_table(table)
        logger.info(f"Table {table_id} created")


def upload_merchants_to_bigquery(merchants: list):
    """Upload merchant data to BigQuery."""
    if not merchants:
        logger.warning("No merchants to upload")
        return

    client = get_bigquery_client()
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    # Add scraped_at timestamp
    for merchant in merchants:
        merchant["scraped_at"] = datetime.utcnow().isoformat()

    try:
        errors = client.insert_rows_json(table_id, merchants, skip_invalid_rows=False)
        if errors:
            logger.error(f"BigQuery insert errors: {errors}")
            return False
        else:
            logger.info(f"✓ Uploaded {len(merchants)} merchants to BigQuery")
            return True
    except Exception as e:
        logger.error(f"BigQuery upload failed: {e}")
        return False


def get_kecamatan_stats(kecamatan_name: str):
    """Get merchant count for a kecamatan from BigQuery."""
    client = get_bigquery_client()
    query = f"""
    SELECT COUNT(*) as merchant_count
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
    WHERE kecamatan_name = '{kecamatan_name}'
    """
    try:
        result = client.query(query).result()
        count = list(result)[0].merchant_count
        return count
    except Exception as e:
        logger.warning(f"Could not fetch stats from BigQuery: {e}")
        return 0
