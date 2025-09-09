#  Intelligent Product Ingestion: A Multimodal AI Pipeline with BigQuery & Gemini
### This project is a submission for the Kaggle "Go BIG with BigQuery AI" competition. It directly addresses both the AI Architect 🧠 and Multimodal Pioneer 🖼️ approaches.

### Live Demo

https://github.com/user-attachments/assets/47860d50-35d3-47e0-90d3-8a514077fd12


## 1. The Problem: The Unstructured Data Bottleneck
Businesses are drowning in unstructured data, particularly product specification sheets from suppliers in PDF format. Manually extracting product titles, descriptions, technical details, and images into an e-commerce platform is a slow, error-prone, and costly process. This manual bottleneck delays time-to-market for new products and introduces data inconsistencies, holding back business growth.

## 2. The Solution: An Automated Multimodal Pipeline
This project solves the problem by providing a complete, end-to-end web application that automates the entire ingestion process. A user simply uploads a product PDF, and our intelligent pipeline, powered by Google Cloud and BigQuery AI, takes over.

**Key Features:**
**Web-Based UI:** A clean, intuitive interface for uploading product PDFs.

+ **Multimodal Extraction:** Automatically extracts both raw text and all images from the PDF.

+ **AI-Powered Image Classification:** Uses the Gemini Vision model to analyze each extracted image, intelligently distinguishing between actual product photos and irrelevant charts or logos.

+ **AI-Powered Data Structuring:** Leverages BigQuery's `AI.GENERATE_TABLE` function to transform the unstructured wall of text into a clean, structured table with well-defined columns (e.g., `product_title`, `color`, `dimensions`).

+ **Intelligent Data Enrichment:** Uses a BigQuery Remote Function to call an external web service that searches for and finds the product's EAN/UPC code based on its title, enriching the dataset with information not present in the original document.

+ **Interactive Results:** Displays the final, enriched data in a user-friendly product card and a detailed table, with an option to download the results as a CSV file.

## 3. Architecture Overview
The application follows a modern, serverless architecture that is both powerful and cost-effective.

**Workflow:**

1.**Upload:** The user uploads a PDF via the Flask web application.

2. **Multimodal Pre-processing:** The Flask backend extracts all text and images. The Gemini Vision API is called to filter for relevant product images only.

3. **Staging:** The raw text and the URLs of the filtered images are loaded into a staging table in BigQuery.

4. **AI Structuring:** A BigQuery query executes `AI.GENERATE_TABLE`, using a Gemini model to read the raw text and generate a structured table of product attributes.

5. **AI Enrichment:** A final BigQuery query calls a `REMOTE FUNCTION`. This function triggers a secure Cloud Run service that performs a web search to find the EAN/UPC code.

6. **Final Result:** The fully structured and enriched data is returned to the user in the web application.

## 4. BigQuery AI in Action
This project was built from the ground up to showcase the power of AI capabilities integrated directly into BigQuery.

+ `AI.GENERATE_TABLE` (AI Architect 🧠): This is the core of our solution. Instead of complex Python scripts for parsing, we use a single SQL command to pass raw text to a Gemini model and receive a perfectly structured table as the output. This demonstrates how generative AI is becoming a native part of SQL-based data warehousing.

+ `REMOTE FUNCTION` (AI Architect 🧠): We extend BigQuery's capabilities beyond its boundaries. By creating a remote function that calls our secure Cloud Run service, we enrich our internal data with external, real-time information from the web (EAN/UPC codes), creating a more valuable final dataset.

+ Gemini Vision API (Multimodal Pioneer 🖼️): Our solution doesn't just treat images as files to be extracted. By calling the Gemini Vision model, we perform intelligent, AI-driven classification to distinguish valuable product photos from noise. This is a true multimodal approach, where we analyze the content of the unstructured image data to make decisions.

## 5. How to Run This Project
Prerequisites:
+ A Google Cloud Project with Billing enabled.

+ The following APIs enabled: BigQuery, Cloud Storage, Vertex AI, Cloud Run, BigQuery Connection.

+ A service account with appropriate permissions (Editor role is recommended for simplicity).

+ `gcloud` CLI installed and authenticated (`gcloud auth application-default login`).

**Setup & Installation:**
1. **Clone the Repository:**

```bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
cd YOUR_REPO_NAME
```
2. **Set Up Python Virtual Environment:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
3. **Configure Google Cloud Resources:**

+ Create two GCS buckets: one for PDFs, one for public images.

+ Create a BigQuery dataset (e.g., `product_data`) in a multi-region like `us`.

+ Create a Programmable Search Engine to get a Search Engine ID and a Google Cloud API Key.

4. **Deploy the EAN Search Function:**

+ Deploy the code in `main.py` as a new Cloud Run service (e.g., `find-ean-function`).

+ Crucially, set the `SEARCH_API_KEY` and `SEARCH_ENGINE_ID` as environment variables in the Cloud Run service, not in the code.

+ Ensure the entry point is `find_ean`.

5. **Configure BigQuery Connections:**

+ In the BigQuery UI, create two connections in the `us` location:

1. A `Cloud Resource` connection for Vertex AI (e.g., `vertex-ai-connection`).

2. A `Cloud Function` connection for the EAN search (e.g., `ean-search-connection`).

+ Grant the necessary IAM roles to their respective service accounts (`Vertex AI User` and `Cloud Functions Invoker`).

**Running the Application:**
1. **Run the Flask Web App:**
```bash
flask run
```
or alternatively, you can still use python function
```bash
python app.py
```
2. Open your browser to `http://12_7.0.0.1:5000` to use the application.

## 6. Future Improvements
+ **Event-Driven Architecture:** The pipeline could be fully automated by using a Cloud Function that triggers on new file uploads to the GCS bucket.

+ **Advanced Error Handling:** Implement a dead-letter queue for PDFs that fail processing for manual review.

+ **Vector Search for Similar Products:** The extracted product descriptions could be converted into embeddings (`ML.GENERATE_EMBEDDING`) to enable vector search for finding semantically similar products.

This project was developed by Mattia Mangia.
