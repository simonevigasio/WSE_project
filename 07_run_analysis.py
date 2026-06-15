import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

INPUT_CSV = "outputs/final_dataset_with_financial_flag.csv"
PLOT_DIR = "outputs/plots"

def analyze():
    print("--- Step 7: Final Results Analysis (Financial Flag Dataset) ---")
    if not os.path.exists(INPUT_CSV):
        print(f"Error: {INPUT_CSV} missing. Run step 5 first.")
        return
    
    os.makedirs(PLOT_DIR, exist_ok=True)
    
    df = pd.read_csv(INPUT_CSV)
    print(f"Dataset shape: {df.shape}")
    
    # 1. Target Distribution
    total = len(df)
    noms = df['target_oscar_nom'].sum()
    print(f"Total Movies: {total} | Oscar Nominated: {noms} ({noms/total*100:.2f}%)")
    
    # --- BOOLEAN FEATURES ANALYSIS ---
    
    # A. Financial Data Flag
    if 'has_financial_data' in df.columns:
        print("\n--- Boolean Feature: Financial Data Availability ---")
        fin_impact = df.groupby('has_financial_data')['target_oscar_nom'].mean() * 100
        print(fin_impact)
        
        plt.figure(figsize=(8, 6))
        sns.barplot(x=fin_impact.index, y=fin_impact.values, hue=fin_impact.index, palette='viridis', legend=False)
        plt.title('Nomination Rate by Financial Data Availability')
        plt.ylabel('Nomination Rate (%)')
        plt.savefig(f"{PLOT_DIR}/bool_financial_data.png")
        plt.close()

    # B. Adaptation Flag
    if 'is_adaptation' in df.columns:
        print("\n--- Boolean Feature: Is Adaptation ---")
        adapt_impact = df.groupby('is_adaptation')['target_oscar_nom'].mean() * 100
        print(adapt_impact)
        
        plt.figure(figsize=(8, 6))
        sns.barplot(x=adapt_impact.index, y=adapt_impact.values, hue=adapt_impact.index, palette='coolwarm', legend=False)
        plt.title('Nomination Rate by Adaptation Status')
        plt.ylabel('Nomination Rate (%)')
        plt.savefig(f"{PLOT_DIR}/bool_is_adaptation.png")
        plt.close()

    # --- CATEGORICAL FEATURES ANALYSIS ---

    # C. Production Company
    print("\n--- Categorical Feature: Production Company ---")
    top_studios = df['production_company'].value_counts().head(15).index
    studio_stats = df[df['production_company'].isin(top_studios)].groupby('production_company')['target_oscar_nom'].mean() * 100
    studio_stats = studio_stats.sort_values(ascending=False)
    
    plt.figure(figsize=(12, 8))
    sns.barplot(x=studio_stats.values, y=studio_stats.index, hue=studio_stats.index, palette='magma', legend=False)
    plt.title('Nomination Rate by Top 15 Production Companies')
    plt.xlabel('Nomination Rate (%)')
    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/cat_production_company.png")
    plt.close()

    # D. Primary Country
    print("\n--- Categorical Feature: Primary Country ---")
    top_countries = df['primary_country'].value_counts().head(15).index
    country_stats = df[df['primary_country'].isin(top_countries)].groupby('primary_country')['target_oscar_nom'].mean() * 100
    country_stats = country_stats.sort_values(ascending=False)
    
    plt.figure(figsize=(12, 8))
    sns.barplot(x=country_stats.values, y=country_stats.index, hue=country_stats.index, palette='plasma', legend=False)
    plt.title('Nomination Rate by Top 15 Countries')
    plt.xlabel('Nomination Rate (%)')
    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/cat_primary_country.png")
    plt.close()

    # E. Original Language
    print("\n--- Categorical Feature: Original Language ---")
    top_langs = df['original_language'].value_counts().head(15).index
    lang_stats = df[df['original_language'].isin(top_langs)].groupby('original_language')['target_oscar_nom'].mean() * 100
    lang_stats = lang_stats.sort_values(ascending=False)
    
    plt.figure(figsize=(12, 8))
    sns.barplot(x=lang_stats.values, y=lang_stats.index, hue=lang_stats.index, palette='inferno', legend=False)
    plt.title('Nomination Rate by Top 15 Languages')
    plt.xlabel('Nomination Rate (%)')
    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/cat_original_language.png")
    plt.close()

    # F. Month
    print("\n--- Categorical Feature: Month ---")
    month_order = [str(i) for i in range(1, 13)] + ['Unknown_month']
    monthly = df.groupby('month')['target_oscar_nom'].mean() * 100
    monthly = monthly.reindex(month_order)
    
    plt.figure(figsize=(12, 6))
    sns.lineplot(x=monthly.index, y=monthly.values, marker='o', color='royalblue')
    plt.title('Nomination Rate by Release Month')
    plt.ylabel('Nomination Rate (%)')
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig(f"{PLOT_DIR}/cat_month.png")
    plt.close()

    # --- TOP CORRELATIONS ---
    print("\n--- Top Numerical Correlations ---")
    num_df = df.select_dtypes(include=['number'])
    corr = num_df.corr()['target_oscar_nom'].sort_values(ascending=False)
    top_corr = corr.iloc[1:11]
    print(top_corr)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x=top_corr.values, y=top_corr.index, hue=top_corr.index, palette='rocket', legend=False)
    plt.title('Top 10 Feature Correlations with Oscar Nomination')
    plt.savefig(f"{PLOT_DIR}/top_correlations.png")
    plt.close()

    print(f"\nAll analysis complete. Graphs saved to '{PLOT_DIR}'.")

if __name__ == "__main__":
    analyze()
