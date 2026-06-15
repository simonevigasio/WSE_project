import json
import pandas as pd
import os
from collections import Counter

# --- Configuration & Paths ---
RAW_MOVIES = "data/raw_movies.jsonl"
PRESTIGE_DATA = "data/talent_prestige.json"
OSCAR_CATEGORIES = "data/oscar_categories.json"
LABELS_MAP = "data/wikidata_english_labels.json"

OUTPUT_FINANCIALS = "outputs/final_dataset_with_financials.csv"
OUTPUT_FLAG = "outputs/final_dataset_with_financial_flag.csv"

# --- Helper Functions ---

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
    Extracts the earliest valid year and month from a list of Wikidata time strings.
    Returns (year, month) where month can be 'Unknown_month'.
    """
    year, month = None, None
    if not isinstance(release_dates, list):
        return None, "Unknown_month"

    # Sort dates to evaluate the chronologically earliest ones first
    clean_dates = sorted([d for d in release_dates if d and isinstance(d, str)])
    
    for rd in clean_dates:
        try:
            parts = rd.lstrip("+").split("-")
            potential_year = int(parts[0])
            potential_month = int(parts[1])
            
            # Filter for the relevant study period (2011-2026)
            if 2011 <= potential_year <= 2026:
                year = potential_year
                # If we find a valid month, we are done. Otherwise, keep looking for a better date.
                if 1 <= potential_month <= 12:
                    month = potential_month
                    break 
        except (ValueError, IndexError):
            continue
            
    return year, (month if month else "Unknown_month")

def calculate_prestige(talent_ids, reference_year, prestige_map):
    """
    Calculates cumulative Oscar prestige (wins/noms) for a list of talent IDs 
    strictly BEFORE the movie's release year to prevent data leakage.
    """
    total_prestige = 0
    for t_id in talent_ids:
        if t_id in prestige_map:
            # Count events where the award year is less than the movie release year
            total_prestige += sum(1 for event in prestige_map[t_id] 
                                 if event.get('year') and int(event['year']) < reference_year)
    return total_prestige

def clean_numeric(val):
    """Safely converts Wikidata numeric strings (e.g. '+15000000') to floats."""
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

    with open(RAW_MOVIES, "r") as f:
        for line in f:
            if not line.strip(): continue
            movie = json.loads(line)
            q_id = movie["movie_id"]
            
            # 1. Target Labeling (1 if nominated/won an Oscar)
            awards_claims = movie.get("P1411", []) + movie.get("P166", [])
            target = 1 if any(cat in oscar_cats for cat in awards_claims) else 0
            
            # 2. Temporal Features
            year, month = extract_release_date(movie.get("P577", []))
            if not year: continue # Skip movies outside our temporal scope

            # 3. Talent Prestige (Time-Aware)
            director_prestige = calculate_prestige(movie.get("P57", []), year, prestige_map)
            cast_prestige = calculate_prestige(movie.get("P161", [])[:5], year, prestige_map)

            # 4. Categorical Feature Resolution
            movie_genres = [labels.get(g_id, g_id) for g_id in movie.get("P136", [])]
            for g in movie_genres: genre_counter[g] += 1

            studio_id = next(iter(movie.get("P272", [None])), None)
            country_id = next(iter(movie.get("P495", [None])), None)
            lang_id = next(iter(movie.get("P364", [None])), None)

            # 5. Row Construction
            rows.append({
                "movie_id": q_id, 
                "title": labels.get(q_id, q_id), 
                "year": year, 
                "month": month,
                "duration": clean_numeric(next(iter(movie.get("P2047", [None])), None)),
                "budget": clean_numeric(next(iter(movie.get("P2130", [None])), None)),                        
                "box_office": clean_numeric(next(iter(movie.get("P2142", [None])), None)),                
                "is_adaptation": 1 if "P144" in movie else 0,
                "director_prestige": director_prestige, 
                "cast_prestige": cast_prestige,
                "production_company": labels.get(studio_id, "Other") if studio_id else "Other",                       
                "primary_country": labels.get(country_id) if country_id else None,
                "original_language": labels.get(lang_id) if lang_id else None,
                "genres": movie_genres, 
                "target_oscar_nom": target
            })

    if not rows:
        print("No valid rows built. Check your data inputs.")
        return

    df = pd.DataFrame(rows)

    # --- Data Imputation Logic ---

    # A. Runtime: Median per Genre (Fall back to Global Median)
    df['primary_genre'] = df['genres'].apply(lambda x: x[0] if x else None)
    genre_medians = df.groupby('primary_genre')['duration'].median()
    global_median = df['duration'].median()
    
    def impute_duration(row):
        if pd.notnull(row['duration']): return row['duration']
        genre_val = genre_medians.get(row['primary_genre'])
        if pd.notnull(genre_val): return genre_val
        return global_median

    df['duration'] = df.apply(impute_duration, axis=1)
    df.drop(columns=['primary_genre'], inplace=True)

    # B. Language: Mode Imputation
    if not df['original_language'].mode().empty:
        df['original_language'] = df['original_language'].fillna(df['original_language'].mode()[0])

    # --- Feature Encoding ---

    # One-hot encode the top 20 genres
    top_genres = [g for g, _ in genre_counter.most_common(20)]
    for g in top_genres:
        col_name = f"genre_{g.replace(' ', '_')}"
        df[col_name] = df["genres"].apply(lambda x: 1 if g in x else 0)
    
    df.drop(columns=["genres"], inplace=True)
    
    # --- File Export ---
    os.makedirs("outputs", exist_ok=True)
    
    # Version 1: With Raw Financials (Sparse)
    df.to_csv(OUTPUT_FINANCIALS, index=False)
    print(f"Version 1 (Raw Financials) saved to {OUTPUT_FINANCIALS}")

    # Version 2: With Financial Flag (Complete)
    df_flag = df.copy()
    df_flag['has_financial_data'] = (df_flag['budget'].notnull() | df_flag['box_office'].notnull()).astype(int)
    df_flag.drop(columns=['budget', 'box_office'], inplace=True)
    df_flag.to_csv(OUTPUT_FLAG, index=False)
    print(f"Version 2 (Financial Flag) saved to {OUTPUT_FLAG}")

if __name__ == "__main__":
    build()
