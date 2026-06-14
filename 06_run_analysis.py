import pandas as pd

INPUT_CSV = "outputs/final_dataset.csv"

def analyze():
    print("--- Step 5: Final Results Analysis ---")
    if not os.path.exists(INPUT_CSV):
        print("Error: Dataset missing.")
        return
    df = pd.read_csv(INPUT_CSV)

    # print number of rows and columns
    print(f"Dataset shape: {df.shape}")
    
    # 1. Target distribution
    nom = df['target_oscar_nom'].sum()
    print(f"Total Movies: {len(df)} | Oscar Nominated: {nom} ({nom/len(df)*100:.2f}%)")
    
    # 2. Correlations
    num_df = df.select_dtypes(include=['number'])
    corr = num_df.corr()['target_oscar_nom'].sort_values(ascending=False)
    print("\nTop correlations with Oscar Nom:")
    print(corr.head(10))
    
    # 3. Best months
    monthly = df.groupby('month')['target_oscar_nom'].mean() * 100
    print("\nPercentage of Nom by Month:")
    print(monthly)

if __name__ == "__main__":
    import os
    analyze()
