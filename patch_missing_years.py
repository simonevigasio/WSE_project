import requests
import json
import time

SPARQL_URL = "https://query.wikidata.org/sparql"

# Make sure to update the email so Wikidata knows you are a responsible researcher
HEADERS = {
    'User-Agent': 'OscarBaitResearchProjectPatch/1.0 (simone@domain.edu)',
    'Accept': 'application/json'
}

output_file = "movie_ids_2011_2026.json"
missing_years = [2013, 2018]
newly_fetched_ids = []

# 1. Load your existing 75,130 IDs so we can append to them
try:
    with open(output_file, "r") as f:
        existing_ids = json.load(f)
    print(f"Successfully loaded {len(existing_ids)} existing film IDs from master list.")
except FileNotFoundError:
    print(f"Error: Could not find '{output_file}' in this directory.")
    existing_ids = []

print("\n--- Starting Patch for Missing Years (2013 & 2018) ---")

for year in missing_years:
    print(f"\nProcessing year {year} month-by-month to avoid server timeouts...")
    
    for month in range(1, 13):
        print(f" -> Fetching {year}-{month:02d}...")
        
        # Sub-dividing by month makes the query light, swift, and highly stable
        sparql_query = f"""
        SELECT DISTINCT ?film WHERE {{
          ?film wdt:P31 wd:Q11424.
          ?film wdt:P577 ?releaseDate.
          FILTER(YEAR(?releaseDate) = {year} && MONTH(?releaseDate) = {month})
        }}
        """
        
        success = False
        retries = 3
        while retries > 0 and not success:
            try:
                response = requests.get(SPARQL_URL, params={'format': 'json', 'query': sparql_query}, headers=HEADERS)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', {}).get('bindings', [])
                    month_ids = [item['film']['value'].split('/')[-1] for item in results]
                    newly_fetched_ids.extend(month_ids)
                    print(f"    Done! Found {len(month_ids)} films.")
                    success = True
                elif response.status_code == 429:
                    print("    [Rate Limit Hit] Sleeping for 15 seconds before retry...")
                    time.sleep(15)
                    retries -= 1
                elif response.status_code in [502, 503, 504]:
                    print(f"    [Server Error {response.status_code}] Wikidata is busy. Backing off for 20 seconds...")
                    time.sleep(20)
                    retries -= 1
                else:
                    print(f"    Failed with status code {response.status_code}. Skipping month.")
                    break
            except Exception as e:
                print(f"    Network exception: {e}. Retrying...")
                time.sleep(10)
                retries -= 1
                
        # Small sleep between months to stay compliant with usage policies
        time.sleep(1.5)

# 2. Combine, Deduplicate, and Merge
combined_ids = list(set(existing_ids + newly_fetched_ids))

print("\n--- Patch Process Finished ---")
print(f"Total new IDs collected from 2013 & 2018: {len(set(newly_fetched_ids))}")
print(f"Updated Master List Grand Total: {len(combined_ids)} unique film Q-IDs.")

# 3. Save the complete master dataset back to file
with open(output_file, "w") as f:
    json.dump(combined_ids, f)

print(f"Successfully updated and overwrote '{output_file}'!")