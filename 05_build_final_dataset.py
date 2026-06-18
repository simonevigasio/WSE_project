import json
import pandas as pd
import os
from collections import Counter

# --- Configuration & Paths ---
RAW_MOVIES = "data/raw_movies.jsonl"
PRESTIGE_DATA = "data/talent_prestige.json"
OSCAR_CATEGORIES = "data/oscar_categories.json"
LABELS_MAP = "data/wikidata_english_labels.json"

OUTPUT_FINAL = "outputs/final_dataset.csv"

# --- Helper Functions ---

def check_eligibility(movie):
    """
    Evaluates a movie based ONLY on properties present in the SPARQL dump.
    Returns (True, "Pass") or (False, "Reason for failure").
    """
    # 1. Sub-type Exclusions (P31 / P279)
    # Q501311 = TV Movie, Q24862 = Short Film, Q7889 = Video Game Q506240
    instances = movie.get('P31', []) + movie.get('P279', [])
    invalid_types = {'Q501311', 'Q24862', 'Q7889'}
    if any(t in invalid_types for t in instances):
        return False, "Failed: Is a TV Movie/Short/Game"
        
    # 2. Genre Exclusions (P136)
    # Q561136 = Pornographic film, Q505809 = Adult film
    genres = movie.get('P136', [])
    invalid_genres = {'Q561136', 'Q505809'}
    if any(g in invalid_genres for g in genres):
        return False, "Failed: Adult Genre"

    # 3. Runtime Gate (P2047)
    runtimes = movie.get('P2047', [])
    if runtimes:
        has_valid_runtime = False
        for r in runtimes:
            try:
                # Strip the '+' sign and convert to float
                val = float(r.replace('+', ''))
                if val > 40:
                    has_valid_runtime = True
                    break
            except ValueError:
                continue
        
        # If runtimes are listed but NONE are > 40, it's a short film
        if not has_valid_runtime:
            return False, "Failed: Runtime under 40 mins"

    # 4. Country of Origin Gate (P495)
    countries = movie.get('P495', [])
    if countries: 
        top_nations = {'Q30', 'Q145', 'Q142', 'Q183', 'Q38', 'Q408', 'Q16', 'Q884', 'Q96'}
        if not any(c in top_nations for c in countries):
            return False, "Failed: Outside Top 9 Nations"

    # 5. Commercial Proxy (Must have either a budget, box office, or known studio)
    has_budget = 'P2130' in movie
    has_box_office = 'P2142' in movie
    has_studio = 'P272' in movie
    if not (has_budget or has_box_office or has_studio):
        return False, "Failed: No Commercial Footprint (No Studio/Budget/Box Office)"

    return True, "Pass"

def load_json_resources():
    """Load all necessary JSON mapping files."""
    if not all(os.path.exists(p) for p in [OSCAR_CATEGORIES, PRESTIGE_DATA, LABELS_MAP]):
        raise FileNotFoundError("Supporting data maps (Oscars, Prestige, or Labels) are missing.")
    
    with open(OSCAR_CATEGORIES, "r") as f: oscar_cats = set(json.load(f))
    with open(PRESTIGE_DATA, "r") as f: prestige_map = json.load(f)
    with open(LABELS_MAP, "r") as f: labels = json.load(f)
    
    return oscar_cats, prestige_map, labels

def extract_release_date(release_dates):
    """
    Extracts the year and month from the earliest valid Wikidata time string.
    Returns (year, month) where month can be 'unknown'.
    """
    if not isinstance(release_dates, list):
        return None, "unknown"

    # Sort dates to evaluate the chronologically earliest ones first
    clean_dates = sorted([d for d in release_dates if d and isinstance(d, str)])
    
    for rd in clean_dates:
        try:
            parts = rd.lstrip("+").split("-")
            potential_year = int(parts[0])
            potential_month = int(parts[1])
            
            # Filter for the relevant study period (2011-2026)
            if 2011 <= potential_year <= 2026:
                # We found the earliest valid date. Use it and stop.
                month = potential_month if 1 <= potential_month <= 12 else "unknown"
                return potential_year, month
        except (ValueError, IndexError):
            continue
            
    return None, "unknown"

def calculate_prestige(talent_ids, reference_year, prestige_map):
    """Calculates cumulative Oscar prestige (wins/noms) strictly BEFORE the movie's release year."""
    total_prestige = 0
    for t_id in talent_ids:
        if t_id in prestige_map:
            total_prestige += sum(1 for event in prestige_map[t_id] 
                                 if event.get('year') and int(event['year']) < reference_year)
    return total_prestige

def clean_numeric(val):
    """Safely converts Wikidata numeric strings to floats."""
    if val is None: return None
    try:
        return float(str(val).lstrip("+"))
    except (ValueError, TypeError):
        return None

# --- Main Processing Pipeline ---

def build():
    print("--- Step 5: Building Final ML Dataset ---")
    
    try:
        oscar_cats, prestige_map, labels = load_json_resources()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    rows = []
    genre_counter = Counter()
    country_counter = Counter()
    lang_counter = Counter()
    studio_counter = Counter()
    
    total_processed = 0
    drop_reasons = Counter()

    with open(RAW_MOVIES, "r") as f:
        for line in f:
            if not line.strip(): continue
            total_processed += 1
            movie = json.loads(line)
            q_id = movie["movie_id"]
            
            # --- Eligibility Check (Merged from Step 2b) ---
            is_eligible, reason = check_eligibility(movie)
            if not is_eligible:
                drop_reasons[reason] += 1
                continue
            
            # 1. Target Labeling
            awards_claims = movie.get("P1411", []) + movie.get("P166", [])
            target = 1 if any(cat in oscar_cats for cat in awards_claims) else 0
            
            # 2. Temporal Features
            year, month = extract_release_date(movie.get("P577", []))
            if not year: 
                drop_reasons["Failed: No valid release year"] += 1
                continue

            # 3. Talent Prestige
            director_prestige = calculate_prestige(movie.get("P57", []), year, prestige_map)
            cast_prestige = calculate_prestige(movie.get("P161", [])[:5], year, prestige_map)

            # 4. Multi-value Feature Resolution
            movie_genres = [labels.get(g_id, g_id) for g_id in movie.get("P136", [])]
            for g in movie_genres: genre_counter[g] += 1

            movie_countries = [labels.get(c_id, c_id) for c_id in movie.get("P495", [])]
            for c in movie_countries: country_counter[c] += 1

            movie_langs = [labels.get(l_id, l_id) for l_id in movie.get("P364", [])]
            for l in movie_langs: lang_counter[l] += 1

            movie_studios = [labels.get(s_id, s_id) for s_id in movie.get("P272", [])]
            for s in movie_studios: studio_counter[s] += 1

            # 5. Row Construction
            rows.append({
                "movie_id": q_id, 
                "title": labels.get(q_id, q_id), 
                "year": year, 
                "month": month,
                "duration": clean_numeric(next(iter(movie.get("P2047", [None])), None)),
                "budget_raw": clean_numeric(next(iter(movie.get("P2130", [None])), None)),                        
                "box_office_raw": clean_numeric(next(iter(movie.get("P2142", [None])), None)),                
                "is_adaptation": 1 if "P144" in movie else 0,
                "director_prestige": director_prestige, 
                "cast_prestige": cast_prestige,
                "genres": movie_genres, 
                "countries": movie_countries,
                "languages": movie_langs,
                "studios": movie_studios,
                "target_oscar_nom": target
            })

    print(f"Total Raw Movies: {total_processed}")
    print(f"Total Eligible: {len(rows)}")
    if drop_reasons:
        print("--- Drop Reasons ---")
        for reason, count in drop_reasons.most_common():
            print(f" - {count} films -> {reason}")

    if not rows:
        print("No valid rows built.")
        return

    df = pd.DataFrame(rows)

    # --- Data Imputation Logic: Duration ---
    # We use all genres to estimate runtime. 
    # 1. Flatten the dataframe to calculate medians for every individual genre
    genre_duration_map = df.explode('genres').groupby('genres')['duration'].median().to_dict()
    global_median = df['duration'].median()
    
    def impute_duration(row):
        if pd.notnull(row['duration']): 
            return row['duration']
        
        # If we have genres, take the average of their respective medians
        movie_genres = row.get('genres', [])
        if movie_genres:
            genre_vals = [genre_duration_map.get(g) for g in movie_genres if pd.notnull(genre_duration_map.get(g))]
            if genre_vals:
                return sum(genre_vals) / len(genre_vals)
        
        # Fallback to global median if no genres or no data found
        return global_median

    df['duration'] = df.apply(impute_duration, axis=1)

    # --- Binary Encoding for Multi-value Features ---
    def encode_multi(dataframe, counter, column_name, prefix, top_n=20):
        top_items = [item for item, _ in counter.most_common(top_n)]
        top_items_set = set(top_items)

        # Binary flags for top N
        for item in top_items:
            clean_item = str(item).replace(' ', '_').replace('/', '_').replace('-', '_').replace('.', '')
            dataframe[f"{prefix}_{clean_item}"] = dataframe[column_name].apply(lambda x: 1 if item in x else 0)
        
        # Binary flag for "Other or Unknown"
        # Set to 1 if: 
        # a) the list is empty (Unknown) 
        # b) any item in the list is NOT in the top N (Other)
        def check_other(vals):
            if not vals: return 1
            return 1 if any(v not in top_items_set for v in vals) else 0
            
        dataframe[f"{prefix}_other_or_unknown"] = dataframe[column_name].apply(check_other)
        return dataframe

    df = encode_multi(df, genre_counter, 'genres', 'genre', top_n=35)
    df = encode_multi(df, country_counter, 'countries', 'country', top_n=10)
    df = encode_multi(df, lang_counter, 'languages', 'lang', top_n=10)
    
    # --- Studio Feature Engineering: Is Major Studio ---
    top_studios = [item for item, _ in studio_counter.most_common(20)]
    top_studios_set = set(top_studios)
    df['is_major_studio'] = df['studios'].apply(lambda x: 1 if any(s in top_studios_set for s in x) else 0)

    # --- One-Hot Encoding for Months ---
    possible_months = [str(i) for i in range(1, 13)] + ['unknown']
    for m in possible_months:
        df[f"month_{m}"] = (df['month'].astype(str) == m).astype(int)

    # --- Create Financial Flag & Final Clean ---
    df['has_financial_data'] = (df['budget_raw'].notnull() | df['box_office_raw'].notnull()).astype(int)
    
    # Drop intermediate and sparse columns
    df.drop(columns=["genres", "countries", "languages", "studios", "budget_raw", "box_office_raw", "month"], inplace=True)
    
    # --- File Export ---
    os.makedirs("outputs", exist_ok=True)
    df.to_csv(OUTPUT_FINAL, index=False)
    print(f"Final dataset saved to {OUTPUT_FINAL} ({len(df)} rows).")

if __name__ == "__main__":
    build()
