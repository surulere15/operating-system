import pandas as pd
from catboost import CatBoostRegressor
from sklearn.metrics import roc_auc_score, accuracy_score
from sklearn.model_selection import train_test_split
from pathlib import Path

# Load model
model_path = Path('models/virality_model.cbm')
model = CatBoostRegressor()
model.load_model(str(model_path))

# Generate synthetic data (same distribution as training)
def make_fake_data(rows=2000):
    import numpy as np
    rng = np.random.default_rng(123)
    df = pd.DataFrame({
        'duration_sec': rng.integers(5, 180, size=rows),
        'views': rng.integers(0, 20000, size=rows),
        'likes': rng.integers(0, 5000, size=rows),
        'shares': rng.integers(0, 500, size=rows),
        'comments': rng.integers(0, 200, size=rows),
        'avg_watch_pct': rng.random(rows) * 100,
        'trend_interest': rng.random(rows) * 100,
    })
    df['virality'] = ((df['views'] > 1000) & (df['trend_interest'] > 50)).astype(int)
    return df

# Load data, split, evaluate
df = make_fake_data()
X = df.drop(columns=['virality'])
y = df['virality']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
# Predict on test set
probs = model.predict(X_test)
roc = roc_auc_score(y_test, probs)
acc = accuracy_score(y_test, (probs > 0.5).astype(int))
print('AUC:', roc)
print('Accuracy:', acc)
