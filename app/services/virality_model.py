# app/services/virality_model.py
"""Simple virality prediction helper.

Only a scaffolding – the full training logic will be added later.
"""

import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from catboost import CatBoostRegressor

DB_URL = os.getenv("DATABASE_URL", "postgresql://viralbees:dev-password-change-in-prod@postgres:5432/viralbees")
MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "models" / "virality_model.cbm"

# ------------------------------------------------------------------
# Load historic data
# ------------------------------------------------------------------

def _load_historic(limit: int = 10000) -> pd.DataFrame:
    """Return dataframe with video metadata + analytics."""
    engine = create_engine(DB_URL)
    query = text(
        """
        SELECT v.id, v.duration, v.created_at, a.views, a.likes, a.shares, a.comments, a.avg_watch_pct
        FROM videos v
        JOIN video_analytics a ON a.video_id = v.id
        ORDER BY v.created_at DESC
        LIMIT :limit
        """
    )
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"limit": limit})
    return df

# ------------------------------------------------------------------
# Training – placeholder
# ------------------------------------------------------------------

def train_model():
    df = _load_historic(limit=5000)
    # Dummy label – note: implement real logic later
    df["virality"] = (df["views"] > 1000).astype(int)
    X = df.drop(columns=["virality"])
    y = df["virality"]
    model = CatBoostRegressor(iterations=200, learning_rate=0.1, loss_function="Logloss", verbose=False)
    model.fit(X, y)
    model.save_model(MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_model()
