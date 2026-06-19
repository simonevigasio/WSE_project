import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from plot_config import apply_plot_config

apply_plot_config()

df = pd.read_csv("outputs/final_dataset.csv")

correlations = df.drop(columns=['movie_id', 'title']).corr()['target_oscar_nom'].sort_values(ascending=False)
print("Top Positive Correlations:")
print(correlations.head(11))
print("\nTop Negative Correlations:")
print(correlations.tail(10))

top_pos = correlations.iloc[1:8]
top_neg = correlations.tail(7)
combined_corr = pd.concat([top_pos, top_neg]).sort_values()

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
fig, ax = plt.subplots(figsize=(10, 8))

colors = ['#d9534f' if x < 0 else '#5cb85c' for x in combined_corr.values]

combined_corr.plot(kind='barh', color=colors, ax=ax)
ax.set_title('Top Features Correlated with Oscar Nomination (target_oscar_nom)', fontsize=14, pad=15)
ax.set_xlabel('Correlation Coefficient', fontsize=12)
ax.set_ylabel('Features', fontsize=12)
plt.tight_layout()

plt.savefig('outputs/plots/oscar_feature_correlations.png', dpi=300)
plt.close()
print("Correlation plot saved successfully.")