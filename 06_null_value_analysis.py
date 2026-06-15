import pandas as pd
import os

FILES_TO_ANALYZE = [
    "outputs/final_dataset_with_financials.csv",
    "outputs/final_dataset_with_financial_flag.csv"
]

def analyze_nulls():
    print("--- Step 6: NULL Value Analysis ---")
    
    for file_path in FILES_TO_ANALYZE:
        if not os.path.exists(file_path):
            print(f"Error: {file_path} missing. Run step 5 first.")
            continue

        print(f"\n>>> Analyzing: {file_path}")
        df = pd.read_csv(file_path)
        
        print(f"Dataset contains {len(df)} rows and {len(df.columns)} columns.")
        
        null_counts = df.isnull().sum()
        null_percentages = (null_counts / len(df)) * 100
        
        null_df = pd.DataFrame({
            'Column': null_counts.index,
            'Null Count': null_counts.values,
            'Percentage': null_percentages.values
        })
        
        # Filter to show only columns with at least one null
        null_df = null_df[null_df['Null Count'] > 0].sort_values(by='Null Count', ascending=False)
        
        if null_df.empty:
            print("Status: SUCCESS! No NULL values found in this version.")
        else:
            print("Missing Data Summary:")
            print(null_df.to_string(index=False))
            
            if "budget" in null_df['Column'].values:
                print("\nNote: High missingness in financial data is common in Wikidata.")

if __name__ == "__main__":
    analyze_nulls()
