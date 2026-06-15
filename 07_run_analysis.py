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
    
    # 2. Financial Data Impact
    if 'has_financial_data' in df.columns:
        fin_impact = df.groupby('has_financial_data')['target_oscar_nom'].mean() * 100
        print("\nOscar Nomination Rate based on Financial Data Availability:")
        print(f" - No Financial Data: {fin_impact.get(0, 0):.2f}%")
        print(f" - Has Financial Data: {fin_impact.get(1, 0):.2f}%")
        
        # Plot Financial Impact
        plt.figure(figsize=(8, 6))
        sns.barplot(x=fin_impact.index, y=fin_impact.values, hue=fin_impact.index, palette='viridis', legend=False)
        plt.title('Oscar Nomination Rate by Financial Data Availability')
        plt.ylabel('Nomination Rate (%)')
        plt.xlabel('Has Financial Data (0=No, 1=Yes)')
        plt.savefig(f"{PLOT_DIR}/financial_impact.png")
        plt.close()

    # 3. Correlations
    num_df = df.select_dtypes(include=['number'])
    corr = num_df.corr()['target_oscar_nom'].sort_values(ascending=False)
    
    print("\nTop Correlations with Oscar Nomination:")
    top_corr = corr.iloc[1:11]
    print(top_corr)
    
    # Plot Top Correlations
    plt.figure(figsize=(10, 6))
    sns.barplot(x=top_corr.values, y=top_corr.index, hue=top_corr.index, palette='magma', legend=False)
    plt.title('Top 10 Features Correlated with Oscar Nomination')
    plt.xlabel('Correlation Coefficient')
    plt.savefig(f"{PLOT_DIR}/top_correlations.png")
    plt.close()
    
    # 4. Temporal Analysis (Month)
    print("\nNomination Rate by Release Month:")
    # Define month order for plotting
    month_order = [str(i) for i in range(1, 13)] + ['Unknown_month']
    
    # Calculate monthly rates
    monthly = df.groupby('month')['target_oscar_nom'].mean() * 100
    
    # Reindex to ensure order
    monthly = monthly.reindex(month_order)
    print(monthly)
    
    # Plot Monthly Trends
    plt.figure(figsize=(12, 6))
    sns.lineplot(x=monthly.index, y=monthly.values, marker='o', color='royalblue')
    plt.title('Oscar Nomination Rate by Release Month')
    plt.ylabel('Nomination Rate (%)')
    plt.xlabel('Month')
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig(f"{PLOT_DIR}/monthly_trends.png")
    plt.close()

    print(f"\nGraphs have been saved to the '{PLOT_DIR}' directory.")

if __name__ == "__main__":
    analyze()
