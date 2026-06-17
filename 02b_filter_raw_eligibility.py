import json
import os
from collections import Counter

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

def filter_dataset(input_filepath, output_filepath):
    print(f"Reading from {input_filepath}...")
    total_processed = 0
    total_eligible = 0
    
    # Counter to track exactly why films are dropped
    drop_reasons = Counter()
    
    with open(input_filepath, 'r') as infile, open(output_filepath, 'w') as outfile:
        for line in infile:
            if not line.strip():
                continue
                
            total_processed += 1
            movie = json.loads(line)
            
            is_eligible, reason = check_eligibility(movie)
            
            if is_eligible:
                total_eligible += 1
                outfile.write(json.dumps(movie) + '\n')
            else:
                drop_reasons[reason] += 1
                
    print("\n--- FILTER RESULTS ---")
    print(f"Total Raw Movies: {total_processed}")
    print(f"Total Oscar-Eligible Movies: {total_eligible}")
    print(f"Total Noise Eliminated: {total_processed - total_eligible}\n")
    
    print("--- WHY MOVIES WERE DROPPED ---")
    for reason, count in drop_reasons.most_common():
        print(f"{count} films -> {reason}")

if __name__ == "__main__":
    INPUT_JSONL = "data/raw_movies.jsonl" 
    OUTPUT_JSONL = "data/eligible_raw_movies.jsonl"
    
    if os.path.exists(INPUT_JSONL):
        filter_dataset(INPUT_JSONL, OUTPUT_JSONL)
    else:
        print(f"Error: Could not find {INPUT_JSONL}")