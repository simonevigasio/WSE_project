import json

output_file = "movie_ids_2011_2026.json"

try:
    # 1. Load the final list of IDs
    with open(output_file, "r") as f:
        movie_ids = json.load(f)
    
    total_ids = len(movie_ids)
    # A set only allows unique elements, so casting it to a set drops duplicates
    unique_ids = len(set(movie_ids)) 
    
    print("--- Data Integrity Check ---")
    print(f"Total elements counted in JSON: {total_ids}")
    print(f"Unique IDs counted (using set): {unique_ids}")
    
    # 2. Compare the sizes
    if total_ids == unique_ids:
        print("\n✅ Success! There are absolutely NO duplicate IDs in your list.")
        print("Your dataset is perfectly deduplicated and ready for feature extraction.")
    else:
        duplicate_count = total_ids - unique_ids
        print(f"\n⚠️ Warning! Found {duplicate_count} duplicate IDs inside the file.")
        
        # Optional: Clean it right now if duplicates somehow slipped in
        cleaned_ids = list(set(movie_ids))
        with open(output_file, "w") as f:
            json.dump(cleaned_ids, f)
        print(f"🔧 Automatically fixed! Cleaned list saved with {len(cleaned_ids)} IDs.")

except FileNotFoundError:
    print(f"Error: Master file '{output_file}' not found. Make sure you are running this in the correct folder.")