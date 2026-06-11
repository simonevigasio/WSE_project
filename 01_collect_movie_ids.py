import requests
import json
import time
import os

# Configuration
SPARQL_URL = "https://query.wikidata.org/sparql"
HEADERS = {
    'User-Agent': 'OscarBaitResearch/2.0 (simone@domain.edu)',
    'Accept': 'application/json'
}
START_YEAR = 2023
END_YEAR = 2023
OUTPUT_FILE = "data/movie_ids.json"

def collect():
    print("--- Step 1: Collecting Movie IDs from Wikidata ---")
    all_movie_ids = []
    
    # Check for existing data
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            all_movie_ids = json.load(f)
        print(f"Found existing list with {len(all_movie_ids)} IDs. Refreshing...")

    for year in range(START_YEAR, END_YEAR + 1):
        print(f"Querying films for {year}...")
        query = f"""
        SELECT DISTINCT ?film WHERE {{
          ?film wdt:P31 wd:Q11424.
          ?film wdt:P577 ?releaseDate.
          FILTER(YEAR(?releaseDate) = {year})
          
          # Filter for USA or European countries
          ?film wdt:P495 ?country.
          ?country (wdt:P30*) ?continent.
          
          FILTER(?country = wd:Q30 || ?continent = wd:Q46)
        }}
        """
        try:
            response = requests.get(SPARQL_URL, params={'format': 'json', 'query': query}, headers=HEADERS)
            if response.status_code == 200:
                results = response.json().get('results', {}).get('bindings', [])
                year_ids = [item['film']['value'].split('/')[-1] for item in results]
                print(f" -> Retrieved {len(year_ids)} films for {year}.")   
                print(f" -> First 5: {year_ids[:5]}")
                all_movie_ids.extend(year_ids)
                print(f" -> Found {len(year_ids)} films.")
            else:
                print(f" -> Error {response.status_code}")
        except Exception as e:
            print(f" -> Exception: {e}")
        time.sleep(1)

    all_movie_ids = list(set(all_movie_ids))
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_movie_ids, f)
    print(f"Saved {len(all_movie_ids)} unique IDs to {OUTPUT_FILE}")

if __name__ == "__main__":
    collect()
