"""run_train_refined.py

Complete end‑to‑end script that:
1️⃣ Generates a synthetic video‑analytics dataset (or pulls real data later).
2️⃣ Engineers TF‑IDF text features + numeric engagement features.
3️⃣ Trains a CatBoost classifier to predict virality.
4️⃣ Evaluates AUC & accuracy on a hold‑out set.
5️⃣ Persists the trained model to `models/virality_refined.cbm`.
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score
from catboost import CatBoostRegressor
from sklearn.feature_extraction.text import TfidfVectorizer

# ------------------------------------------------------------------
# 1️⃣ Synthetic data (replace with real DB extraction when ready)
# ------------------------------------------------------------------
def generate_synthetic_data(n: int = 5000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    titles = ["Amazing AI video" if rng.random() < 0.3 else "Daily vlog" for _ in range(n)]
    descriptions = ["Learn about AI breakthroughs" if rng.random() < 0.25 else "Just a regular day" for _ in range(n)]
    duration_sec = rng.integers(5, 180, size=n)
    views = rng.integers(0, 20000, size=n)
    likes = rng.integers(0, 5000, size=n)
    shares = rng.integers(0, 500, size=n)
    comments = rng.integers(0, 200, size=n)
    avg_watch_pct = rng.random(n) * 100
    trend_interest = rng.random(n) * 100  # Simulated Google‑Trends score (0‑100)

    df = pd.DataFrame({
        "title": titles,
        "description": descriptions,
        "duration_sec": duration_sec,
        "views": views,
        "likes": likes,
        "shares": shares,
        "comments": comments,
        "avg_watch_pct": avg_watch_pct,
        "trend_interest": trend_interest,
    })
    # Target: virality = high views AND high trend interest
    df["virality"] = ((df["views"] > 1000) & (df["trend_interest"] > 50)).astype(int)
    return df

# ------------------------------------------------------------------
# 2️⃣ Feature engineering – TF‑IDF + numeric features
# ------------------------------------------------------------------
def engineer_features(df: pd.DataFrame) -> tuple[pd.DataFrame, TfidfVectorizer]:
    # --- Text cleaning ------------------------------------------------
    df["clean_title"] = df["title"].str.lower().str.replace(r"[^a-z0-9\s]", " ", regex=True)
    df["clean_desc"] = df["description"].str.lower().str.replace(r"[^a-z0-9\s]", " ", regex=True)
    combined = df["clean_title"] + " " + df["clean_desc"]
    # --- TF‑IDF (max 20 features for speed) --------------------------
    tfidf = TfidfVectorizer(max_features=20)
    tfidf_mat = tfidf.fit_transform(combined).toarray()
    tfidf_cols = [f"tfidf_{i}" for i in range(tfidf_mat.shape[1])]
    tfidf_df = pd.DataFrame(tfidf_mat, columns=tfidf_cols)
    # --- Numeric engineered metrics -----------------------------------
    df["duration_bin"] = pd.cut(df["duration_sec"], bins=[0,30,60,120,180], labels=False)
    df["engagement_ratio"] = (df["likes"] + df["shares"] + df["comments"]) / (df["views"] + 1)
    # Assemble final dataframe for modeling
    feature_df = pd.concat([
        tfidf_df,
        df[["duration_sec", "duration_bin", "avg_watch_pct", "trend_interest", "engagement_ratio"]]
    ], axis=1)
    return feature_df, tfidf

# ------------------------------------------------------------------
# 3️⃣ Training & evaluation
# ------------------------------------------------------------------
def train_and_evaluate():
    print("🚀 Generating synthetic video-analytics dataset...")
    df = generate_synthetic_data()
    
    print("⚙️ Engineering TF-IDF text features & numeric engagement metrics...")
    X, tfidf = engineer_features(df)
    y = df["virality"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("🏋️ Training CatBoost virality model...")
    # Initialize and train CatBoost
    model = CatBoostRegressor(
        iterations=150,
        learning_rate=0.1,
        depth=6,
        eval_metric="RMSE",
        random_seed=42,
        verbose=10
    )
    model.fit(
        X_train, y_train,
        eval_set=(X_test, y_test),
        use_best_model=True
    )
    
    print("📊 Evaluating model on hold-out test set...")
    probs = model.predict(X_test)
    # Clip probabilities to [0, 1] for metric calculation
    probs_clipped = np.clip(probs, 0, 1)
    
    auc = roc_auc_score(y_test, probs_clipped)
    acc = accuracy_score(y_test, (probs_clipped > 0.5).astype(int))
    
    print(f"\n📈 Evaluation Results:")
    print(f"   - ROC AUC Score: {auc:.4f}")
    print(f"   - Accuracy Score: {acc:.4f}")
    
    # ------------------------------------------------------------------
    # 4️⃣ Persist trained model & vectorizer
    # ------------------------------------------------------------------
    os.makedirs("models", exist_ok=True)
    
    model_path = "models/virality_refined.cbm"
    model.save_model(model_path)
    print(f"💾 CatBoost model saved to: {model_path}")
    
    vec_path = "models/tfidf_vectorizer.pkl"
    with open(vec_path, "wb") as f:
        pickle.dump(tfidf, f)
    print(f"💾 TF-IDF Vectorizer saved to: {vec_path}")

if __name__ == "__main__":
    train_and_evaluate()