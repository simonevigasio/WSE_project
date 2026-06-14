import requests
import json
import os
import time

API_URL = "https://www.wikidata.org/w/api.php"
HEADERS = {'User-Agent': 'OscarBaitResearch/2.0 (simone@domain.edu)', 'Accept': 'application/json'}

CORE_PROPERTIES = {
    "P31": "instance_of", "P577": "release_date", "P136": "genre", "P57": "director",
    "P161": "cast_member", "P272": "production_company", "P2047": "duration",
    "P2142": "box_office", "P495": "country_of_origin", "P364": "original_language",
    "P144": "based_on", "P1411": "nominated_for", "P166": "award_received", 
    "P2130": "cost"
}

INPUT_FILE = "data/movie_ids.json"
OUTPUT_FILE = "data/raw_movies.jsonl"

def parse_snak_value(datavalue):
    if not datavalue: return None
    v_type = datavalue.get('type')
    val = datavalue.get('value')
    if v_type == 'wikibase-entityid': return val.get('id')
    if v_type == 'quantity': return val.get('amount')
    if v_type == 'time': return val.get('time')
    return str(val)

def fetch():
    print("--- Step 2: Fetching Targeted Movie Features ---")

    # check for existing data
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} missing.")
        return

    # read all movie IDs
    with open(INPUT_FILE, "r") as f:
        all_ids = json.load(f)
    
    # check for already processed IDs to allow resuming
    processed_ids = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            for line in f:
                if line.strip():
                    processed_ids.add(json.loads(line)["movie_id"])
        print(f"Resuming. {len(processed_ids)} already done.")

    # filter out already processed IDs
    remaining = [mid for mid in all_ids if mid not in processed_ids]

    chunk_size = 50
    with open(OUTPUT_FILE, "a") as out_f:
        for i in range(0, len(remaining), chunk_size):

            # Fetch a chunk of movie IDs
            chunk = remaining[i:i+chunk_size]

            # Prepare API request
            params = {'action': 'wbgetentities', 'ids': "|".join(chunk), 'props': 'claims', 'format': 'json'}
            
            try:
                resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
                if resp.status_code == 200:
                    entities = resp.json().get('entities', {})
                    for q_id in chunk:
                        claims = entities.get(q_id, {}).get('claims', {})
                        movie_data = {"movie_id": q_id}
                        for prop_id in CORE_PROPERTIES:
                            if prop_id in claims:
                                vals = [parse_snak_value(s.get('mainsnak', {}).get('datavalue')) for s in claims[prop_id]]
                                movie_data[prop_id] = [v for v in vals if v]
                        out_f.write(json.dumps(movie_data) + "\n")
                if i % 500 == 0: 
                    print(f"Progress: {len(processed_ids) + i}/{len(all_ids)}")
                time.sleep(0.5)
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)
    print("Movie features fetched.")

if __name__ == "__main__":
    fetch()
