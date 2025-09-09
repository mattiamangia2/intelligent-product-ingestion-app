# queries.py

# This query uses AI to structure the raw text from a single product.
# It finds the relevant row in the staging table using the unique product_id.
def run_structuring_query(client, product_id):
    sql = f"""
    CREATE OR REPLACE TABLE `{client.project}.product_data.structured_products_temp` AS
    SELECT *
    FROM AI.GENERATE_TABLE(
        MODEL `{client.project}.product_data.gemini_model`,
        (
            SELECT product_id, raw_text AS prompt
            FROM `{client.project}.product_data.staging_product_data`
            WHERE product_id = '{product_id}'
        ),
        STRUCT(
            'product_title STRING, description STRING, color STRING, material STRING, battery STRING, power STRING, dimensions STRING' AS output_schema
        )
    );
    """
    client.query(sql).result() # Wait for the job to complete


# This query joins the structured data with image URLs and EAN codes.
# It now specifically handles the case where no results are found.
def run_enrichment_query(client, product_id):
    sql = f"""
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
        `{client.project}.product_data.find_ean`(sp.product_title) AS ean_upc
    FROM `{client.project}.product_data.structured_products_temp` AS sp
    JOIN `{client.project}.product_data.staging_product_data` AS sd
        ON sp.product_id = sd.product_id
    WHERE sp.product_id = '{product_id}';
    """
    query_job = client.query(sql)
    results = query_job.result()

    # --- THIS IS THE FIX ---
    # Check if the query returned any rows at all.
    if results.total_rows == 0:
        # If not, it means the AI failed to structure the data. Return None.
        return None

    # If we have rows, process the first one (there should only be one).
    final_data = None
    for row in results:
        final_data = dict(row.items())
        break # We only care about the first result
    
    return final_data


