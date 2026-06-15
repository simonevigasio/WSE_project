import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import os

# --- Configuration ---
INPUT_CSV = "outputs/final_dataset.csv"

def train_model():
    print("--- Step 8: Training Baseline Logistic Regression ---")
    if not os.path.exists(INPUT_CSV):
        print(f"Error: {INPUT_CSV} missing. Run the pipeline first.")
        return

    df = pd.read_csv(INPUT_CSV)
    
    # 1. Feature Selection
    # Drop non-feature columns
    drop_cols = ["movie_id", "title", "target_oscar_nom"]
    X = df.drop(columns=drop_cols)
    y = df["target_oscar_nom"]
    
    print(f"Dataset Shape: {df.shape}")
    print(f"Target Distribution:\n{y.value_counts(normalize=True) * 100}")
    
    # 2. Train/Test Split
    # Using stratify to ensure minority class is represented in both sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # 3. Scaling
    # Logistic Regression is sensitive to feature scale
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 4. Model Training
    # 'class_weight="balanced"' is crucial for this dataset (<1% target)
    # It penalizes mistakes on the minority class more heavily.
    model = LogisticRegression(
        class_weight='balanced', 
        max_iter=1000, 
        random_state=42
    )
    
    print("\nTraining model with class_weight='balanced'...")
    model.fit(X_train_scaled, y_train)
    
    # 5. Evaluation
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]
    
    print("\n>>> Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    print("\n>>> Classification Report:")
    # We focus on the minority class (1) performance
    print(classification_report(y_test, y_pred))
    
    roc_auc = roc_auc_score(y_test, y_prob)
    print(f"\nROC-AUC Score: {roc_auc:.4f}")
    
    # 6. Feature Importance (Top 10)
    importance = pd.DataFrame({
        'Feature': X.columns,
        'Coefficient': model.coef_[0]
    }).sort_values(by='Coefficient', ascending=False)
    
    print("\n>>> Top 10 Positive Predictors for Oscar Nomination:")
    print(importance.head(10).to_string(index=False))
    
    print("\n>>> Top 10 Negative Predictors for Oscar Nomination:")
    print(importance.tail(10).to_string(index=False))

if __name__ == "__main__":
    train_model()
