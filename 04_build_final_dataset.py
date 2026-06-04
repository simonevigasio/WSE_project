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
    with open(OSCAR_CATEGORIES, "r") as f: oscar_cats = set(json.load(f))
    with open(PRESTIGE_DATA, "r") as f: prestige_map = json.load(f)
    with open(LABELS_MAP, "r") as f: labels = json.load(f)

    rows = []
    genre_counter = Counter()

    with open(RAW_MOVIES, "r") as f:
        for line in f:
            movie = json.loads(line)
            q_id = movie["movie_id"]
            
            # Target
            target = 1 if any(c in oscar_cats for c in movie.get("P1411", []) + movie.get("P166", [])) else 0
            
            # Year/Month
            rd = movie.get("P577", [None])[0]
            year, month = None, None
            if rd:
                try:
                    parts = rd.lstrip("+").split("-")
                    year, month = int(parts[0]), (int(parts[1]) if int(parts[1]) > 0 else None)
                except: pass
            
            if not year: continue

            # Prestige
            def get_prestige(ids):
                p = 0
                for i in ids:
                    if i in prestige_map:
                        p += sum(1 for e in prestige_map[i] if e['year'] and int(e['year']) < year)
                return p

            d_prestige = get_prestige(movie.get("P57", []))
            c_prestige = get_prestige(movie.get("P161", [])[:5])

            # Genres
            movie_genres = [labels.get(g_id, g_id) for g_id in movie.get("P136", [])]
            for g in movie_genres: genre_counter[g] += 1

            rows.append({
                "movie_id": q_id, "title": labels.get(q_id, q_id), "year": year, "month": month,
                "duration": next(iter(movie.get("P2047", [None])), None),
                "budget": next(iter(movie.get("P2142", [None])), None),
                "is_adaptation": 1 if "P144" in movie else 0,
                "director_prestige": d_prestige, "cast_prestige": c_prestige,
                "primary_country": labels.get(movie.get("P495", [None])[0], "Unknown"),
                "primary_language": labels.get(movie.get("P364", [None])[0], "Unknown"),
                "genres": movie_genres, "target_oscar_nom": target
            })

    df = pd.DataFrame(rows)
    top_genres = [g for g, _ in genre_counter.most_common(20)]
    for g in top_genres:
        df[f"genre_{g.replace(' ', '_')}"] = df["genres"].apply(lambda x: 1 if g in x else 0)
    df.drop(columns=["genres"], inplace=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Final dataset saved to {OUTPUT_CSV} ({len(df)} rows).")

if __name__ == "__main__":
    build()
