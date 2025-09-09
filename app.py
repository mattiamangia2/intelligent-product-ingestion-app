from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
import pandas as pd
from google.cloud import storage, bigquery
import os
import uuid
# THE FIX IS HERE: We removed the non-existent 'get_final_product'
from queries import run_structuring_query, run_enrichment_query

# --- CONFIGURATION ---
PROJECT_ID = "kaggle-bigqueryai"
PDF_BUCKET_NAME = "kaggle-pdf-product-sheets"
IMAGE_BUCKET_NAME = "kaggle-extracted-images"
DATASET_ID = "product_data"
STAGING_TABLE_ID = "staging_product_data"
UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- GOOGLE CLOUD CLIENTS (Initialized once) ---
storage_client = storage.Client(project=PROJECT_ID)
bq_client = bigquery.Client(project=PROJECT_ID)
image_bucket = storage_client.bucket(IMAGE_BUCKET_NAME)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process-pdf', methods=['POST'])
def process_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if file and allowed_file(file.filename):
        try:
            upload_id = str(uuid.uuid4())
            
            # --- 1. PDF PROCESSING ---
            pdf_content = file.read()
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            
            raw_text = "".join(page.get_text() for page in doc)
            image_urls = []
            for page_num, page in enumerate(doc):
                for img_index, img in enumerate(page.get_images(full=True)):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_filename = f"{upload_id}_page{page_num+1}_img{img_index}.png"
                    
                    image_blob = image_bucket.blob(image_filename)
                    image_blob.upload_from_string(image_bytes, content_type='image/png')
                    image_urls.append(image_blob.public_url)

            # --- 2. LOAD TO BIGQUERY STAGING ---
            data_for_bq = { 'product_id': upload_id, 'raw_text': raw_text }
            if image_urls:
                 data_for_bq['image_url_1'] = image_urls[0]

            df = pd.DataFrame([data_for_bq])
            table_ref = f"{PROJECT_ID}.{DATASET_ID}.{STAGING_TABLE_ID}"
            job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
            bq_client.load_table_from_dataframe(df, table_ref, job_config=job_config).result()

            # --- 3. RUN BIGQUERY AI PIPELINE ---
            run_structuring_query(bq_client, upload_id)
            final_data = run_enrichment_query(bq_client, upload_id)
            
            if not final_data:
                 return jsonify({'error': 'Failed to process data in BigQuery. The AI model may have returned no data for this PDF.'}), 500

            return jsonify(final_data)

        except Exception as e:
            print(f"An error occurred: {e}")
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

