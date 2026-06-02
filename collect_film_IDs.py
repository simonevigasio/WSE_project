import requests
import json
import time

# Wikidata SPARQL Endpoint URL
SPARQL_URL = "https://query.wikidata.org/sparql"

# Crucial: Wikidata requires a descriptive User-Agent header. 
# Replace the email placeholder with yours to avoid random API blocks.
HEADERS = {
    'User-Agent': 'OscarBaitResearchProject/1.0 (your_email@domain.edu)',
    'Accept': 'application/json'
}

start_year = 2011
end_year = 2026
all_movie_ids = []

print("--- Step 1: Starting Movie ID Collection from Wikidata ---")

for year in range(start_year, end_year + 1):
    print(f"Querying films for the year: {year}...")
    
    # Optimised query pulling only the film node to keep it lightning-fast
    sparql_query = f"""
    SELECT DISTINCT ?film WHERE {{
      ?film wdt:P31 wd:Q11424.      # Instance of: Film
      ?film wdt:P577 ?releaseDate.  # Has a publication date
      FILTER(YEAR(?releaseDate) = {year})
    }}
    """
    
    try:
        response = requests.get(SPARQL_URL, params={'format': 'json', 'query': sparql_query}, headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', {}).get('bindings', [])
            
            year_ids = []
            for item in results:
                # Extracts the full URL (e.g., 'http://www.wikidata.org/entity/Q105658212')
                film_url = item['film']['value']
                # Clean it up to extract just the Q-ID string (e.g., 'Q105658212')
                q_id = film_url.split('/')[-1]
                year_ids.append(q_id)
                
            print(f" -> Found {len(year_ids)} films.")
            all_movie_ids.extend(year_ids)
            
        elif response.status_code == 429:
            print(" -> [Rate Limit Hit] Sleeping for 10 seconds...")
            time.sleep(10)
            # Simple 1-time retry for stability
            response = requests.get(SPARQL_URL, params={'format': 'json', 'query': sparql_query}, headers=HEADERS)
            if response.status_code == 200:
                # Process retry
                results = response.json().get('results', {}).get('bindings', [])
                all_movie_ids.extend([item['film']['value'].split('/')[-1] for item in results])
        else:
            print(f" -> Failed to fetch {year} (Status Code: {response.status_code})")
            
    except Exception as e:
        print(f" -> Exception encountered for year {year}: {e}")
        
    # Respectful 1-second sleep delay to stick to Wikidata's rate-limiting policy
    time.sleep(1)

# Deduplicate in case a movie has multiple release dates crossing calendar years
all_movie_ids = list(set(all_movie_ids))

print("\n--- Phase 1 Complete ---")
print(f"Total Unique Film Q-IDs gathered: {len(all_movie_ids)}")

# Save the master list to a local JSON file
output_file = "movie_ids_2011_2026.json"
with open(output_file, "w") as f:
    json.dump(all_movie_ids, f)

print(f"Saved master ID list to: '{output_file}'")