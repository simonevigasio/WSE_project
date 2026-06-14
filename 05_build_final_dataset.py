import json
import pandas as pd
import os
from collections import Counter

RAW_MOVIES = "data/raw_movies.jsonl"
PRESTIGE_DATA = "data/talent_prestige.json"
OSCAR_CATEGORIES = "data/oscar_categories.json"
LABELS_MAP = "data/wikidata_english_labels.json"
OUTPUT_CSV = "outputs/final_dataset.csv"

def build():
    print("--- Step 4: Building Final ML Dataset ---")
    if not os.path.exists(OSCAR_CATEGORIES) or not os.path.exists(PRESTIGE_DATA) or not os.path.exists(LABELS_MAP):
        print("Error: Supporting data maps are missing.")
        return

    with open(OSCAR_CATEGORIES, "r") as f: oscar_cats = set(json.load(f))
    with open(PRESTIGE_DATA, "r") as f: prestige_map = json.load(f)
    with open(LABELS_MAP, "r") as f: labels = json.load(f)

    rows = []
    genre_counter = Counter()

    with open(RAW_MOVIES, "r") as f:
        for line in f:
            if not line.strip(): continue
            movie = json.loads(line)
            q_id = movie["movie_id"]
            
            # 1. Target (Did this movie ever win or get nominated for an Oscar?)
            target = 1 if any(c in oscar_cats for c in movie.get("P1411", []) + movie.get("P166", [])) else 0
            
            # 2. Release Year/Month Extraction
            rd = movie.get("P577", [None])[0]
            year, month = None, None
            if rd:
                try:
                    parts = rd.lstrip("+").split("-")
                    year, month = int(parts[0]), (int(parts[1]) if int(parts[1]) > 0 else None)
                except: pass
            
            if not year: continue

            # 3. Time-Aware Talent Prestige calculation (No future leakage)
            def get_prestige(ids):
                p = 0
                for i in ids:
                    if i in prestige_map:
                        p += sum(1 for e in prestige_map[i] if e.get('year') and int(e['year']) < year)
                return p

            d_prestige = get_prestige(movie.get("P57", []))
            c_prestige = get_prestige(movie.get("P161", [])[:5])

            # 4. Process Genres
            movie_genres = [labels.get(g_id, g_id) for g_id in movie.get("P136", [])]
            for g in movie_genres: genre_counter[g] += 1

            # Helper function to convert numeric strings (like "+15000000") safely
            def clean_numeric(val):
                if val is None: return None
                try:
                    return float(str(val).lstrip("+"))
                except:
                    return None

            # 5. Extract features according to new CORE_PROPERTIES
            raw_duration = next(iter(movie.get("P2047", [None])), None)
            raw_box_office = next(iter(movie.get("P2142", [None])), None)
            raw_budget = next(iter(movie.get("P2130", [None])), None)         # Fixed: Now uses P2130 (cost)
            
            # Production Company (P272) Extraction
            primary_studio_id = next(iter(movie.get("P272", [None])), None)
            primary_studio = labels.get(primary_studio_id, "Unknown") if primary_studio_id else "Unknown"

            # 1. Fetch the arrays safely (defaulting to an empty array if missing)
            raw_countries = movie.get("P495", [])
            raw_languages = movie.get("P364", [])

            # 2. Extract index 0 ONLY if the array actually contains items
            country_id = raw_countries[0] if len(raw_countries) > 0 else None
            lang_id = raw_languages[0] if len(raw_languages) > 0 else None

            # 3. Build your row dictionary safely
            rows.append({
                "movie_id": q_id, 
                "title": labels.get(q_id, q_id), 
                "year": year, 
                "month": month,
                "duration": clean_numeric(raw_duration),
                "budget": clean_numeric(raw_budget),                        
                "box_office": clean_numeric(raw_box_office),                
                "is_adaptation": 1 if "P144" in movie else 0,
                "director_prestige": d_prestige, 
                "cast_prestige": c_prestige,
                "production_company": primary_studio,                       
                "primary_country": labels.get(country_id, "Unknown") if country_id else "Unknown",
                "original_language": labels.get(lang_id, "Unknown") if lang_id else "Unknown",
                "genres": movie_genres, 
                "target_oscar_nom": target
            })

    if not rows:
        print("No valid rows built. Check your data inputs.")
        return

    df = pd.DataFrame(rows)
    
    # 6. One-hot encode the top 20 genres
    top_genres = [g for g, _ in genre_counter.most_common(20)]
    for g in top_genres:
        df[f"genre_{g.replace(' ', '_')}"] = df["genres"].apply(lambda x: 1 if g in x else 0)
    
    df.drop(columns=["genres"], inplace=True)
    
    # Ensure parent output directory exists
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Final dataset saved to {OUTPUT_CSV} ({len(df)} rows).")

if __name__ == "__main__":
    build()