import pandas as pd
import os

INPUT_CSV = "outputs/final_dataset.csv"

def analyze_binary_frequency():
    print("--- Step 7: Binary Feature Frequency Analysis ---")
    if not os.path.exists(INPUT_CSV):
        print(f"Error: {INPUT_CSV} missing. Run step 5 first.")
        return
    
    df = pd.read_csv(INPUT_CSV)
    
    # Identify binary columns
    # We include columns that have only 0 and 1, or those with known binary prefixes
    binary_prefixes = ['genre_', 'country_', 'lang_', 'studio_', 'month_', 'is_', 'has_', 'target_']
    binary_cols = [c for c in df.columns if any(c.startswith(pre) for pre in binary_prefixes)]
    
    # Further filter to ensure they only contain 0 and 1 (just in case)
    binary_cols = [c for c in binary_cols if df[c].dropna().isin([0, 1]).all()]
    
    print(f"Analyzing {len(binary_cols)} binary features in a dataset of {len(df)} rows.\n")
    
    results = []
    for col in binary_cols:
        count_1s = (df[col] == 1).sum()
        percentage = (count_1s / len(df)) * 100
        
        # Categorize for easier viewing
        category = "Other"
        for pre in binary_prefixes:
            if col.startswith(pre):
                category = pre.rstrip('_')
                break
        
        results.append({
            'Category': category,
            'Feature': col,
            'Count (1s)': count_1s,
            'Percentage (%)': round(percentage, 4)
        })
    
    res_df = pd.DataFrame(results)
    
    # Sort by Category and then by frequency
    res_df = res_df.sort_values(by=['Category', 'Count (1s)'], ascending=[True, False])
    
    # Display summary by category
    for cat in res_df['Category'].unique():
        print(f"\n>>> Category: {cat}")
        sub_df = res_df[res_df['Category'] == cat].drop(columns='Category')
        # Show top 5 and the 'other_or_unknown' if it exists
        top_n = sub_df.head(5)
        other = sub_df[sub_df['Feature'].str.contains('other_or_unknown|Unknown_month')]
        
        display_df = pd.concat([top_n, other]).drop_duplicates()
        print(display_df.to_string(index=False))

    # Save full results for reference
    OUTPUT_REPORT = "outputs/binary_feature_frequencies.csv"
    res_df.to_csv(OUTPUT_REPORT, index=False)
    print(f"\nFull frequency report saved to {OUTPUT_REPORT}")

if __name__ == "__main__":
    analyze_binary_frequency()
