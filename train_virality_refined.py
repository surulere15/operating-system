"""train_virality_refined.py

This script creates a synthetic video dataset, enriches it with text‑based and numeric features, trains a CatBoost classifier to predict virality, evaluates the model using AUC, and saves the model for later inference.

Replace the synthetic data generator with a real DB query when you move to production.
"""

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score
from catboost import CatBoostRegressor
from sklearn.feature_extraction.text import TfidfVectorizer

# ------------------------------------------------------------------
# Synthetic data generation (placeholder – replace with real extraction)
# ------------------------------------------------------------------

def generate_synthetic_data(n: int = 5000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    # Simple categorical titles/descriptions
    titles = ["Amazing AI video" if rng.random() < 0.3 else "Daily vlog" for _ in range(n)]
    descriptions = ["Learn about AI breakthroughs" if rng.random() < 0.25 else "Just a regular day" for _ in range(n)]
    duration_sec = rng.integers(5, 180, size=n)
    views = rng.integers(0, 20000, size=n)
    likes = rng.integers(0, 5000, size=n)
    shares = rng.integers(0, 500, size=n)
    comments = rng.integers(0, 200, size=n)
    avg_watch_pct = rng.random(n) * 100
    trend_interest = rng.random(n) * 100  # Simulated trend interest score (0‑100)

    df = pd.DataFrame(
        {
            "title": titles,
            "description": descriptions,
            "duration_sec": duration_sec,
            "views": views,
            "likes": likes,
            "shares": shares,
            "comments": comments,
            "avg_watch_pct": avg_watch_pct,
            "trend_interest": trend_interest,
        }
    )
    # Binary virality label: high views AND high trend interest
    df["virality"] = ((df["views"] > 1000) & (df["trend_interest"] > 50)).astype(int)
    return df

# ------------------------------------------------------------------
# Feature engineering
# ------------------------------------------------------------------

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    # Clean & lower‑case text
    df["clean_title"] = df["title"].str.lower().str.replace(r"[^a-z0-9\s]", " ", regex=True)
    df["clean_desc"] = df["description"].str.lower().str.replace(r"[^a-z0-9\s]", " ", regex=True)
    combined = df["clean_title"] + " " + df["clean_desc"]

    # TF‑IDF vectorization, limited to 20 features for speed
    tfidf = TfidfVectorizer(max_features=20)
    tfidf_mat = tfidf.fit_transform(combined).toarray()
    tfidf_cols = [f"tfidf_{i}" for i in range(tfidf_mat.shape[1])]
    tfidf_df = pd.DataFrame(tfidf_mat, columns=tfidf_cols)

    # Numeric feature engineering
    df["duration_bin"] = pd.cut(df["duration_sec"], bins=[0, 30, 60, 120, 180], labels=False)
    df["engagement_ratio"] = (df["likes"] + df["shares"] + df["comments"]) / (df["views"] + 1)

    # Assemble feature set
    features = pd.concat([tfidf_df, df[["duration_sec", "duration_bin", "avg_watch_pct", "trend_interest", "engagement_ratio"]]], axis=1)
    return features

# ------------------------------------------------------------------
# Training & evaluation
# ------------------------------------------------------------------

def train_and_evaluate():
    df = generate_synthetic_data()
    X = engineer_features(df)
    y = df["virality"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

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

    preds = model.predict(X_test)
    preds_clipped = np.clip(preds, 0, 1)
    auc = roc_auc_score(y_test, preds_clipped)
    acc = accuracy_score(y_test, (preds_clipped > 0.5).astype(int))

    print(f"ROC AUC: {auc:.4f}")
    print(f"Accuracy: {acc:.4f}")

    os.makedirs("models", exist_ok=True)
    model.save_model("models/virality_refined.cbm")
    print("Model saved successfully!")

if __name__ == "__main__":
    train_and_evaluate()