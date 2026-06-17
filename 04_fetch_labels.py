import json
import os
import requests
import time

RAW_MOVIES = "data/eligible_raw_movies.jsonl"
OUTPUT_LABELS = "data/wikidata_english_labels.json"
API_URL = "https://www.wikidata.org/w/api.php"
HEADERS = {'User-Agent': 'OscarBaitResearch/2.0 (simone@domain.edu)'}

def fetch_labels():
    print("--- Step 4: Resolving English Labels for All Extracted Entities ---")
    
    if not os.path.exists(RAW_MOVIES):
        print(f"Error: {RAW_MOVIES} missing. Run step 2 first.")
        return

    # 1. Collect all unique Q-IDs across your entire dataset
    unique_qids = set()
    with open(RAW_MOVIES, "r") as f:
        for line in f:
            if not line.strip(): continue
            movie = json.loads(line)
            
            # Add movie ID itself
            unique_qids.add(movie["movie_id"])
            
            # Look inside properties for entity references (IDs starting with 'Q')
            for prop in ["P136", "P57", "P161", "P272", "P495", "P364"]:
                for item in movie.get(prop, []):
                    if str(item).startswith("Q"):
                        unique_qids.add(item)

    print(f"Found {len(unique_qids)} unique entities requiring translation.")

    # Load existing labels if you need to resume an interrupted run
    labels_map = {}
    if os.path.exists(OUTPUT_LABELS):
        with open(OUTPUT_LABELS, "r") as f:
            labels_map = json.load(f)
        print(f"Loaded {len(labels_map)} existing labels from cache.")

    # Filter out entities we already have translations for
    remaining_qids = [q for q in unique_qids if q not in labels_map]
    print(f"{len(remaining_qids)} labels left to download.")

    # 2. Fetch from Wikidata API in batches of 50
    chunk_size = 50
    for i in range(0, len(remaining_qids), chunk_size):
        chunk = remaining_qids[i:i+chunk_size]
        
        params = {
            'action': 'wbgetentities',
            'ids': "|".join(chunk),
            'props': 'labels',
            'languages': 'en',
            'format': 'json'
        }
        
        try:
            resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                entities = resp.json().get('entities', {})
                for q_id in chunk:
                    # Get English value, default to raw Q-ID if no English translation exists
                    label_val = entities.get(q_id, {}).get('labels', {}).get('en', {}).get('value')
                    labels_map[q_id] = label_val if label_val else q_id
            
            if i % 100 == 0:
                print(f"Progress: {i}/{len(remaining_qids)} labels resolved.")
                # Save periodically in case script gets cut off
                with open(OUTPUT_LABELS, "w") as f:
                    json.dump(labels_map, f, indent=2)
                    
            time.sleep(0.5)  # Respect API limits
        except Exception as e:
            print(f"Error fetching batch: {e}")
            time.sleep(5)

    # 3. Final Save
    os.makedirs(os.path.dirname(OUTPUT_LABELS), exist_ok=True)
    with open(OUTPUT_LABELS, "w") as f:
        json.dump(labels_map, f, indent=2)
    print(f"Success! {len(labels_map)} translation labels saved to {OUTPUT_LABELS}")

if __name__ == "__main__":
    fetch_labels()