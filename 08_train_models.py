import pandas as pd
import numpy as np
import torch
import xgboost as xgb
import matplotlib.pyplot as plt
from sklearn.model_selection import StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.metrics import precision_score, recall_score, f1_score
import os

# --- Configuration ---
INPUT_CSV = "outputs/final_dataset.csv"
OUTPUT_PLOT = "outputs/plots/final_filtered_cv_metrics.png"
N_SPLITS = 10
THRESHOLDS = np.linspace(0.01, 0.99, 50) 

# --- Neural Network ---
class OscarNN(torch.nn.Module):
    def __init__(self, input_dim):
        super(OscarNN, self).__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(input_dim, 64),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.2),
            torch.nn.Linear(64, 32),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.2),
            torch.nn.Linear(32, 1)
        )
    def forward(self, x): return self.net(x)

def run_comprehensive_cv():
    print(f"--- Step 8: {N_SPLITS}-Fold Stratified Cross-Validation (Surgical Scaling) ---")
    if not os.path.exists(INPUT_CSV):
        print(f"Error: {INPUT_CSV} missing.")
        return

    df = pd.read_csv(INPUT_CSV)
    
    # Identify feature types
    target_col = "target_oscar_nom"
    non_feature_cols = ["movie_id", "title", target_col]
    
    # Identify feature types
    target_col = "target_oscar_nom"
    non_feature_cols = ["movie_id", "title", target_col]
    
    continuous_features = ["year", "duration", "director_prestige", "cast_prestige"]
    feature_cols = [c for c in df.columns if c not in non_feature_cols]
    binary_features = [c for c in feature_cols if c not in continuous_features]
    
    X = df[feature_cols]
    y = df[target_col].values
    
    # Define ColumnTransformer: scale all continuous numerical features
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), continuous_features),
            ('pass', 'passthrough', binary_features)
        ]
    )
    
    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=42)
    
    results = {
        m: {met: np.zeros((N_SPLITS, len(THRESHOLDS))) for met in ['prec', 'rec', 'f1']} 
        for m in ['Logistic Regression', 'Neural Network', 'XGBoost']
    }

    fold = 0
    for train_idx, val_idx in skf.split(X, y):
        print(f"Processing Fold {fold+1}/{N_SPLITS}...", end='\r')
        X_train_raw, X_val_raw = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        # Apply preprocessor
        X_train_s = preprocessor.fit_transform(X_train_raw)
        X_val_s = preprocessor.transform(X_val_raw)
        
        # 1. Logistic Regression
        lr = LogisticRegression(class_weight='balanced', max_iter=2000, random_state=42)
        lr.fit(X_train_s, y_train)
        p_lr = lr.predict_proba(X_val_s)[:, 1]

        # 2. XGBoost
        spw = (y_train == 0).sum() / (y_train == 1).sum()
        xb = xgb.XGBClassifier(scale_pos_weight=spw, eval_metric='logloss', random_state=42)
        xb.fit(X_train_s, y_train)
        p_xb = xb.predict_proba(X_val_s)[:, 1]

        # 3. Neural Network
        nn = OscarNN(X.shape[1])
        crit = torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor([spw]))
        opt = torch.optim.Adam(nn.parameters(), lr=0.005)
        Xt = torch.FloatTensor(X_train_s)
        yt = torch.FloatTensor(y_train.reshape(-1, 1))
        
        nn.train()
        for _ in range(20): 
            opt.zero_grad()
            crit(nn(Xt), yt).backward()
            opt.step()
        
        nn.eval()
        with torch.no_grad():
            p_nn = torch.sigmoid(nn(torch.FloatTensor(X_val_s))).numpy().flatten()

        # Calculate metrics for each threshold
        for tidx, t in enumerate(THRESHOLDS):
            for m_name, probs in [('Logistic Regression', p_lr), ('XGBoost', p_xb), ('Neural Network', p_nn)]:
                preds = (probs >= t).astype(int)
                results[m_name]['prec'][fold, tidx] = precision_score(y_val, preds, zero_division=0)
                results[m_name]['rec'][fold, tidx] = recall_score(y_val, preds)
                results[m_name]['f1'][fold, tidx] = f1_score(y_val, preds)
        
        fold += 1

    print(f"\nTraining Complete. Generating Plots...")
    
    plt.figure(figsize=(18, 6))
    for i, m_name in enumerate(results.keys()):
        plt.subplot(1, 3, i+1)
        
        # Mean across folds
        mean_prec = np.mean(results[m_name]['prec'], axis=0)
        mean_rec = np.mean(results[m_name]['rec'], axis=0)
        mean_f1 = np.mean(results[m_name]['f1'], axis=0)
        
        plt.plot(THRESHOLDS, mean_prec, label='Precision', color='blue')
        plt.plot(THRESHOLDS, mean_rec, label='Recall', color='green')
        plt.plot(THRESHOLDS, mean_f1, label='F1 Score', color='red', linestyle='--')
        
        best_t = THRESHOLDS[np.argmax(mean_f1)]
        plt.axvline(best_t, color='gray', alpha=0.5, linestyle=':', label=f'Best F1 (T={best_t:.2f})')
        
        plt.title(f"{m_name}\nAvg {N_SPLITS}-Fold Metrics")
        plt.xlabel("Threshold")
        plt.ylabel("Score")
        plt.ylim(0, 1.05)
        plt.legend(fontsize='small')
        plt.grid(True, alpha=0.2)

    plt.tight_layout()
    os.makedirs(os.path.dirname(OUTPUT_PLOT), exist_ok=True)
    plt.savefig(OUTPUT_PLOT)
    print(f"Final results plotted to: {OUTPUT_PLOT}")

if __name__ == "__main__":
    run_comprehensive_cv()
