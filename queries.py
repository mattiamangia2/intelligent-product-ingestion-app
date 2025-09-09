from google.cloud import bigquery

# --- Configuration (Update these values) ---
PROJECT_ID = "kaggle-bigqueryai"
DATASET_ID = "product_data"
STAGING_TABLE_ID = "staging_product_data"
STRUCTURED_TABLE_ID = "structured_products"
FINAL_TABLE_ID = "final_ecommerce_products"
MODEL_NAME = "gemini_model"
REMOTE_FUNCTION_NAME = "find_ean"

# Initialize BigQuery Client
client = bigquery.Client(project=PROJECT_ID)

def run_structuring_query():
    """
    Runs the AI.GENERATE_TABLE query to process all data in the staging table
    and create a new table with structured product information.
    """
    sql = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.{STRUCTURED_TABLE_ID}` AS
    SELECT
      *
    FROM
      AI.GENERATE_TABLE(
        MODEL `{PROJECT_ID}.{DATASET_ID}.{MODEL_NAME}`,
        (
          SELECT
            product_id,
            raw_text AS prompt
          FROM
            `{PROJECT_ID}.{DATASET_ID}.{STAGING_TABLE_ID}`
        ),
        STRUCT(
          'product_title STRING, description STRING, color STRING, material STRING, battery STRING, power STRING, dimensions STRING' AS output_schema
        )
      );
    """
    client.query(sql).result()

def run_enrichment_query():
    """
    Joins the structured data with staging data (for images) and calls the
    remote function to find the EAN code, creating the final product table.
    """
    sql = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.{FINAL_TABLE_ID}` AS
    SELECT
      sp.product_id,
      sp.product_title,
      sp.description,
      sp.color,
      sp.material,
      sp.battery,
      sp.power,
      sp.dimensions,
      sd.image_url_1,
      `{PROJECT_ID}.{DATASET_ID}.{REMOTE_FUNCTION_NAME}`(sp.product_title) AS ean_upc
    FROM
      `{PROJECT_ID}.{DATASET_ID}.{STRUCTURED_TABLE_ID}` AS sp
    JOIN
      `{PROJECT_ID}.{DATASET_ID}.{STAGING_TABLE_ID}` AS sd
      ON sp.product_id = sd.product_id;
    """
    client.query(sql).result()

def get_final_product(product_id):
    """
    Fetches the single, fully enriched row for a given product_id
    from the final table and returns it as a dictionary.
    """
    sql = f"""
    SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{FINAL_TABLE_ID}`
    WHERE product_id = '{product_id}'
    LIMIT 1;
    """
    query_job = client.query(sql)
    results = query_job.result()
    for row in results:
        return dict(row)
    return None
