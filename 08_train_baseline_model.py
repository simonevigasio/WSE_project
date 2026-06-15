import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    precision_recall_curve, roc_curve, auc, f1_score, precision_score, recall_score
)
import os

# --- Configuration ---
INPUT_CSV = "outputs/final_dataset.csv"
OUTPUT_PLOT = "outputs/plots/model_performance.png"

def train_and_visualize():
    print("--- Step 8: Training & Visualizing Baseline Logistic Regression ---")
    if not os.path.exists(INPUT_CSV):
        print(f"Error: {INPUT_CSV} missing. Run the pipeline first.")
        return

    df = pd.read_csv(INPUT_CSV)
    
    # 1. Feature Selection
    drop_cols = ["movie_id", "title", "target_oscar_nom"]
    X = df.drop(columns=drop_cols)
    y = df["target_oscar_nom"]
    
    print(f"Dataset Shape: {df.shape}")
    
    # 2. Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # 3. Scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 4. Model Training
    model = LogisticRegression(
        class_weight='balanced', 
        max_iter=1000, 
        random_state=42
    )
    
    print("\nTraining model with class_weight='balanced'...")
    model.fit(X_train_scaled, y_train)
    
    # 5. Basic Evaluation
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]
    
    print("\n>>> Confusion Matrix (Threshold=0.5):")
    print(confusion_matrix(y_test, y_pred))
    
    print("\n>>> Classification Report (Threshold=0.5):")
    print(classification_report(y_test, y_pred))
    
    # 6. Threshold & Plotting Logic
    print("\nGenerating performance plots...")
    os.makedirs(os.path.dirname(OUTPUT_PLOT), exist_ok=True)
    
    thresholds = np.linspace(0.01, 0.99, 100)
    precisions, recalls, f1s = [], [], []

    for t in thresholds:
        y_pred_t = (y_prob >= t).astype(int)
        precisions.append(precision_score(y_test, y_pred_t, zero_division=0))
        recalls.append(recall_score(y_test, y_pred_t))
        f1s.append(f1_score(y_test, y_pred_t))

    plt.figure(figsize=(15, 5))

    # Plot 1: Metrics vs Threshold
    plt.subplot(1, 3, 1)
    plt.plot(thresholds, precisions, label='Precision')
    plt.plot(thresholds, recalls, label='Recall')
    plt.plot(thresholds, f1s, label='F1 Score', linestyle='--')
    plt.title('Metrics vs. Threshold')
    plt.xlabel('Threshold')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Plot 2: Precision-Recall Curve
    plt.subplot(1, 3, 2)
    p, r, _ = precision_recall_curve(y_test, y_prob)
    plt.plot(r, p, color='purple')
    plt.title('Precision-Recall Curve')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.grid(True, alpha=0.3)

    # Plot 3: ROC Curve
    plt.subplot(1, 3, 3)
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    plt.plot(fpr, tpr, color='darkorange', label=f'AUC = {auc(fpr, tpr):.4f}')
    plt.plot([0, 1], [0, 1], color='navy', linestyle='--')
    plt.title('ROC Curve')
    plt.xlabel('False Positive Rate')
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUTPUT_PLOT)
    print(f"Plots saved to: {OUTPUT_PLOT}")

    # Optimal F1 threshold
    best_idx = np.argmax(f1s)
    print(f"\nOptimal Threshold (max F1): {thresholds[best_idx]:.4f}")
    print(f" -> Best F1: {f1s[best_idx]:.4f} (Prec: {precisions[best_idx]:.2f}, Rec: {recalls[best_idx]:.2f})")

    # 7. Feature Importance (Top 5)
    importance = pd.DataFrame({'Feature': X.columns, 'Coef': model.coef_[0]}).sort_values(by='Coef', ascending=False)
    print("\n>>> Top 5 Predictors:")
    print(importance.head(5).to_string(index=False))

if __name__ == "__main__":
    train_and_visualize()
