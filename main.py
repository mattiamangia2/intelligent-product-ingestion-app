import functions_framework
import requests
import json
import re
import os

@functions_framework.http
def find_ean(request):
    """
    This is a secure Cloud Function that searches for a product's EAN code.
    It reads sensitive API keys from environment variables, not from the code itself.
    """
# --- SECURE METHOD: Read secrets from environment variables ---
    API_KEY = os.environ.get("SEARCH_API_KEY")
    SEARCH_ENGINE_ID = os.environ.get("SEARCH_ENGINE_ID")

    if not API_KEY or not SEARCH_ENGINE_ID:
        print("ERROR: Environment variables for search keys are not set.")
# Return a generic error to avoid exposing internal details
        return json.dumps({'replies': ["Server configuration error"] * len(request.get_json()['calls'])})

    request_json = request.get_json(silent=True)
    replies = []
    for call in request_json['calls']:
        product_title = call[0]
        search_query = f'"{product_title}" EAN code OR UPC code'
        search_url = f"https://www.googleapis.com/customsearch/v1?q={search_query}&key={API_KEY}&cx={SEARCH_ENGINE_ID}"
        try:
            response = requests.get(search_url)
            response.raise_for_status()
            search_results = response.json()
            ean = "EAN not found"
            if "items" in search_results:
                for item in search_results["items"]:
                    snippet = item.get("snippet", "") + item.get("title", "")
                    match = re.search(r'\b\d{12,13}\b', snippet)
                    if match:
                        ean = match.group(0)
                        break
            replies.append(ean)
        except Exception as e:
            print(f"An error occurred during search: {e}")
            replies.append(f"Search error")
            
    return json.dumps({'replies': replies})