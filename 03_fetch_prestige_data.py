import requests
import json
import time

SPARQL_URL = "https://query.wikidata.org/sparql"
HEADERS = {'User-Agent': 'OscarBaitResearch/2.0 (simone@domain.edu)', 'Accept': 'application/json'}

def fetch_prestige():
    print("--- Step 3: Fetching Talent Prestige Data (Oscars) ---")
    
    # 1. Get Oscar Categories
    print("🚀 Fetching Oscar categories...")
    query_cats = "SELECT ?award WHERE { ?award wdt:P31 wd:Q19020. }"
    resp = requests.get(SPARQL_URL, params={'format': 'json', 'query': query_cats}, headers=HEADERS)
    if resp.status_code != 200: return
    awards = [item['award']['value'].split('/')[-1] for item in resp.json()['results']['bindings']]
    awards.append("Q19020")
    with open("data/oscar_categories.json", "w") as f: json.dump(awards, f)

    # 2. Get People for these awards
    prestige_map = {}
    chunk_size = 20
    for i in range(0, len(awards), chunk_size):
        chunk = awards[i:i+chunk_size]
        award_filter = " ".join([f"wd:{a}" for a in chunk])
        query_people = f"""
        SELECT DISTINCT ?person ?award ?date WHERE {{
          VALUES ?award {{ {award_filter} }}
          {{ ?person p:P166 [ps:P166 ?award; pq:P585 ?date]. }}
          UNION
          {{ ?person p:P1411 [ps:P1411 ?award; pq:P585 ?date]. }}
        }}
        """
        print(f" -> Querying chunk {i//chunk_size + 1}...")
        resp = requests.get(SPARQL_URL, params={'format': 'json', 'query': query_people}, headers=HEADERS)
        if resp.status_code == 200:
            for item in resp.json().get('results', {}).get('bindings', []):
                p_id = item['person']['value'].split('/')[-1]
                a_id = item['award']['value'].split('/')[-1]
                year = item.get('date', {}).get('value', "").lstrip("+").split("-")[0]
                if p_id not in prestige_map: prestige_map[p_id] = []
                prestige_map[p_id].append({"award": a_id, "year": year})
        time.sleep(1)

    with open("data/talent_prestige.json", "w") as f: json.dump(prestige_map, f, indent=4)
    print(f"✅ Saved prestige data for {len(prestige_map)} people.")

if __name__ == "__main__":
    fetch_prestige()
