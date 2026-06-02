import requests
import json
import os
import time

API_URL = "https://www.wikidata.org/w/api.php"

# Provide your email to stay compliant with Wikidata's API rules
HEADERS = {
    'User-Agent': 'OscarBaitFeatureHarvester/1.0 (simone@domain.edu)',
    'Accept': 'application/json'
}

input_file = "movie_ids_2011_2026.json"
output_file = "raw_movie_features.jsonl"

# 1. Load Master Movie List
if not os.path.exists(input_file):
    print(f"❌ Error: Master file '{input_file}' not found!")
    exit()

with open(input_file, "r") as f:
    all_movie_ids = json.load(f)

print(f"Loaded {len(all_movie_ids)} movie IDs from master list.")

# 2. Checkpoint System: Figure out what has already been processed
processed_ids = set()
if os.path.exists(output_file):
    with open(output_file, "r") as f:
        for line in f:
            if line.strip():
                try:
                    obj = json.loads(line)
                    processed_ids.add(obj["movie_id"])
                except Exception:
                    pass
    print(f"🔄 Checkpoint found! Already processed {len(processed_ids)} movies. Resuming remaining...")

# Filter out what we already have
remaining_ids = [mid for mid in all_movie_ids if mid not in processed_ids]
print(f"📋 Total movies left to process: {len(remaining_ids)}")

if not remaining_ids:
    print("🎉 All movies are already processed!")
    exit()

# Helper function to extract text/numerical data safely out of complex Wikidata structures
def parse_snak_value(datavalue):
    if not datavalue:
        return None
    v_type = datavalue.get('type')
    val = datavalue.get('value')
    
    if v_type == 'wikibase-entityid':
        return val.get('id')                  # e.g., 'Q130005'
    elif v_type == 'quantity':
        return val.get('amount')              # e.g., '+120'
    elif v_type == 'time':
        return val.get('time')                # e.g., '+2019-12-25T00:00:00Z'
    elif v_type == 'string':
        return val                            # Plain text identifiers
    elif v_type == 'monolingualtext':
        return val.get('text')                # Captures text description
    elif isinstance(val, dict) and 'id' in val:
        return val['id']
    return str(val)

# 3. Main Processing Loop (Processing in optimal chunks of 50 items)
chunk_size = 50
print("\n🚀 Starting feature extraction...")

# Open the file in append mode ('a') so we save live on every iteration
with open(output_file, "a") as out_f:
    for i in range(0, len(remaining_ids), chunk_size):
        chunk = remaining_ids[i:i + chunk_size]
        ids_string = "|".join(chunk)
        
        # Action API payload optimized exclusively for claims data
        params = {
            'action': 'wbgetentities',
            'ids': ids_string,
            'props': 'claims',
            'format': 'json'
        }
        
        success = False
        retries = 3
        while retries > 0 and not success:
            try:
                response = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
                if response.status_code == 200:
                    entities = response.json().get('entities', {})
                    
                    for q_id in chunk:
                        entity = entities.get(q_id, {})
                        claims = entity.get('claims', {})
                        
                        # Dynamically discover and flatten ALL properties present
                        movie_features = {"movie_id": q_id}
                        for prop_id, statements in claims.items():
                            # Extract data from all statements attached to this property (handling arrays)
                            values = []
                            for stmt in statements:
                                mainsnak = stmt.get('mainsnak', {})
                                datavalue = mainsnak.get('datavalue')
                                parsed_val = parse_snak_value(datavalue)
                                if parsed_val is not None:
                                    values.append(parsed_val)
                            
                            # Save clean properties list if values exist
                            if values:
                                movie_features[prop_id] = values
                        
                        # Instantly write out to file
                        out_f.write(json.dumps(movie_features) + "\n")
                        
                    success = True
                    processed_count = len(processed_ids) + i + len(chunk)
                    pct = (processed_count / len(all_movie_ids)) * 100
                    print(f" -> Progress: {processed_count}/{len(all_movie_ids)} films harvested ({pct:.2f}%)")
                    
                elif response.status_code == 429:
                    print(" ⚠️ Throttled (429). Sleeping for 20 seconds...")
                    time.sleep(20)
                    retries -= 1
                else:
                    print(f" ❌ Server responded with code {response.status_code}. Retrying...")
                    time.sleep(5)
                    retries -= 1
            except Exception as e:
                print(f" ⚠️ Connection glitch: {e}. Retrying in 10 seconds...")
                time.sleep(10)
                retries -= 1
                
        # Small delay between chunks to respect Wikidata endpoint capacities
        time.sleep(0.8)

print(f"\n🎉 Step 2 Complete! All structural attributes saved dynamically to '{output_file}'!")