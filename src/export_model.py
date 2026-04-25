import json
import os
import numpy as np
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

print("Caricamento modello e vectorizer...")
vectorizer = joblib.load('models/tfidf_vectorizer.joblib')
model      = joblib.load('models/svm_sport_classifier.joblib')

df = pd.read_csv('data/processed/dataset_sport_cleaned.csv').dropna(subset=['cleaned_text'])
X_train_raw, X_test_raw, y_train, y_test = train_test_split(
    df['cleaned_text'], df['label'], test_size=0.2, random_state=42
)

X_test  = vectorizer.transform(X_test_raw)
scores  = model.decision_function(X_test)
y_pred  = model.predict(X_test)
report  = classification_report(y_test, y_pred, output_dict=True)

# ── Threshold dinamico per classe ─────────────────────────────────────────────
# Per ogni classe: percentile scalato in base a F1-score e numero di campioni
# in training. Classi più accurate e con più dati → percentile più alto
# (soglia più severa). Classi più deboli → percentile più basso (più permissivo).
# Intervallo percentile: [0.5, 2.0]

print("\nCalcolo threshold dinamici per classe...")

f1_vals = {cls: report[cls]['f1-score']         for cls in model.classes_}
n_vals  = {cls: int((y_train == cls).sum())      for cls in model.classes_}

min_f1, max_f1 = min(f1_vals.values()), max(f1_vals.values())
min_n,  max_n  = min(n_vals.values()),  max(n_vals.values())

thresholds = {}
for i, cls in enumerate(model.classes_):
    f1_norm = (f1_vals[cls] - min_f1) / (max_f1 - min_f1 + 1e-9)
    n_norm  = (n_vals[cls]  - min_n)  / (max_n  - min_n  + 1e-9)

    percentile = 0.5 + (0.5 * f1_norm + 0.5 * n_norm) * 1.5

    # Punteggi della classe i per i campioni davvero appartenenti a cls
    class_scores   = scores[y_test.values == cls, i]
    thresholds[cls] = round(float(np.percentile(class_scores, percentile)), 4)

    print(f"   {cls:<12}  f1={f1_vals[cls]:.3f}  n_train={n_vals[cls]}"
          f"  percentile={percentile:.2f}  threshold={thresholds[cls]:.4f}")

# ── Temperature scaling (calibrazione NLL sul test set) ──────────────────────
# Divide gli score per T prima della softmax.
# T < 1 → distribuzione più "affilata" → percentuali più alte sulla classe vincente.
# T ottimale = minimizza la negative log-likelihood sui campioni test.

print("\nCalcolo temperatura ottimale (temperature scaling)...")

y_test_idx = np.array([list(model.classes_).index(c) for c in y_test])

best_T, best_nll = 1.0, float('inf')
for T in np.linspace(0.05, 2.0, 800):
    scaled   = scores / T
    shifted  = scaled - scaled.max(axis=1, keepdims=True)
    exp_s    = np.exp(shifted)
    probs    = exp_s / exp_s.sum(axis=1, keepdims=True)
    nll      = -np.log(probs[np.arange(len(y_test_idx)), y_test_idx] + 1e-10).mean()
    if nll < best_nll:
        best_nll = nll
        best_T   = float(T)

# Mostra l'effetto sul test set
scaled  = scores / best_T
shifted = scaled - scaled.max(axis=1, keepdims=True)
exp_s   = np.exp(shifted)
probs   = exp_s / exp_s.sum(axis=1, keepdims=True)
avg_conf_T1    = np.exp(-(- np.log(
    (lambda s: np.exp(s - s.max(1, keepdims=True)) /
     np.exp(s - s.max(1, keepdims=True)).sum(1, keepdims=True))(scores)
    [np.arange(len(y_test_idx)), y_test_idx] + 1e-10)).mean())
avg_conf_opt   = probs[np.arange(len(y_test_idx)), y_test_idx].mean()
winning_median = np.median(probs.max(axis=1))

print(f"   Temperatura ottimale:  T = {best_T:.4f}")
print(f"   Confidenza media (T=1):    {avg_conf_T1*100:.1f}%")
print(f"   Confidenza media (T={best_T:.2f}): {avg_conf_opt*100:.1f}%")
print(f"   Mediana percentuale vincente: {winning_median*100:.1f}%")

# ── Esportazione ──────────────────────────────────────────────────────────────
os.makedirs('docs', exist_ok=True)
print("\nEsportazione in docs/model_data.json...")
data = {
    "vocabulary": {w: int(i) for w, i in vectorizer.vocabulary_.items()},
    "idf":        [round(v, 6) for v in vectorizer.idf_.tolist()],
    "coef":       [[round(v, 4) for v in row] for row in model.coef_.tolist()],
    "intercept":  model.intercept_.tolist(),
    "classes":      model.classes_.tolist(),
    "thresholds":   thresholds,
    "temperature":  round(best_T, 4),
    "sublinear_tf": bool(vectorizer.sublinear_tf),
}

with open('docs/model_data.json', 'w') as f:
    json.dump(data, f, separators=(',', ':'))

size_kb = os.path.getsize('docs/model_data.json') / 1024
print(f"   Fatto! ({size_kb:.0f} KB)")
