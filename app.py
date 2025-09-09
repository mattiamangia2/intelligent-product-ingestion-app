import os
import uuid
import fitz  # PyMuPDF
from flask import Flask, request, jsonify, render_template
from google.cloud import storage, bigquery
from queries import run_structuring_query, run_enrichment_query, get_final_product

# --- Configuration (Update these values) ---
PROJECT_ID = "kaggle-bigqueryai"
PDF_BUCKET_NAME = "kaggle-pdf-product-sheets"
IMAGE_BUCKET_NAME = "kaggle-extracted-images-us"
DATASET_ID = "product_data"
STAGING_TABLE_ID = "staging_product_data"

# Initialize clients
storage_client = storage.Client(project=PROJECT_ID)
bq_client = bigquery.Client(project=PROJECT_ID)

app = Flask(__name__)

@app.route('/')
def index():
    """Renders the main HTML page."""
    return render_template('index.html')

@app.route('/process-pdf', methods=['POST'])
def process_pdf():
    """
    The main endpoint that handles the entire pipeline:
    1. Receives an uploaded PDF.
    2. Extracts text and images.
    3. Uploads images to GCS.
    4. Loads raw data to a BigQuery staging table.
    5. Runs the BigQuery AI and enrichment queries.
    6. Returns the final, structured data as JSON.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.pdf'):
        try:
            product_id = f"prod_{uuid.uuid4().hex[:8]}"
            pdf_content = file.read()
            
            # --- Phase 1: Ingestion ---
            print(f"Starting ingestion for product_id: {product_id}")
            
            # Extract text and images
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            raw_text = "".join(page.get_text() for page in doc)
            
            image_urls = []
            image_bucket = storage_client.bucket(IMAGE_BUCKET_NAME)
            for page_num, page in enumerate(doc):
                for img_index, img in enumerate(page.get_images(full=True)):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_filename = f"{product_id}_page{page_num+1}_img{img_index}.png"
                    
                    blob = image_bucket.blob(image_filename)
                    blob.upload_from_string(image_bytes, content_type='image/png')
                    image_urls.append(blob.public_url)

            print(f"Found {len(image_urls)} images.")

            # Load to BigQuery Staging Table
            data_for_bq = {'product_id': product_id, 'raw_text': raw_text}
            if image_urls:
                data_for_bq['image_url_1'] = image_urls[0]

            df = pd.DataFrame([data_for_bq])
            table_ref = f"{PROJECT_ID}.{DATASET_ID}.{STAGING_TABLE_ID}"
            job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
            bq_client.load_table_from_dataframe(df, table_ref, job_config=job_config).result()
            print("Staging data loaded to BigQuery.")

            # --- Phase 2: BigQuery AI Processing ---
            print("Running BigQuery AI structuring query...")
            run_structuring_query()
            
            print("Running enrichment query...")
            run_enrichment_query()

            # --- Phase 3: Fetch Final Result ---
            print(f"Fetching final data for {product_id}...")
            final_product_data = get_final_product(product_id)

            if not final_product_data:
                 return jsonify({"error": "Failed to retrieve final product data from BigQuery."}), 500

            return jsonify(final_product_data)

        except Exception as e:
            print(f"An error occurred: {e}")
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Invalid file type, only PDF is allowed"}), 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))