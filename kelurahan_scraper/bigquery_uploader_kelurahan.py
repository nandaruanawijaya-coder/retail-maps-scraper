"""BigQuery uploader for kelurahan-level merchant data."""
import logging
from google.cloud import bigquery

logger = logging.getLogger(__name__)

PROJECT_ID = "ledger-fcc1e"
DATASET_ID = "retail_payment_base"
TABLE_ID = "merchants_gmaps_kelurahan"  # New table for kelurahan-level data


def get_bigquery_client():
    """Get authenticated BigQuery client."""
    return bigquery.Client(project=PROJECT_ID)


def create_table_if_not_exists():
    """Create BigQuery table for kelurahan-level data if it doesn't exist."""
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
        bigquery.SchemaField("kelurahan_id", "STRING"),
        bigquery.SchemaField("kelurahan_name", "STRING"),
        bigquery.SchemaField("kecamatan_name", "STRING"),
        bigquery.SchemaField("kabupaten_name", "STRING"),
        bigquery.SchemaField("provinsi_name", "STRING"),
        bigquery.SchemaField("scraped_at", "TIMESTAMP"),
    ]

    table = bigquery.Table(table_id, schema=schema)
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="scraped_at",
    )
    table.clustering_fields = ["kelurahan_name", "our_category"]

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

    try:
        errors = client.insert_rows_json(table_id, merchants, skip_invalid_rows=False)
        if errors:
            logger.error(f"BigQuery insert errors: {errors}")
            return False
        else:
            logger.info(f"✓ Uploaded {len(merchants)} merchants to BigQuery (kelurahan table)")
            return True
    except Exception as e:
        logger.error(f"BigQuery upload failed: {e}")
        return False
