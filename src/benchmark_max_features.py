"""
Confronto empirico di max_features per TfidfVectorizer + LinearSVC.
Testa 5000, 6000, 7000, 8000, 9000, 10000 e produce grafici comparativi.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report, accuracy_score

_INPUT_FILE = '../data/processed/dataset_sport_cleaned.csv'
_PLOTS_DIR  = '../models/benchmark_plots'
_MAX_FEATURES_LIST = [5000, 6000, 7000, 8000, 9000, 10000]
_SPORTS = ['F1', 'baseball', 'basketball', 'golf', 'rugby', 'soccer', 'tennis']

os.makedirs(_PLOTS_DIR, exist_ok=True)

# ── Caricamento dati ───────────────────────────────────────────────────────────
print("Caricamento dataset...")
df = pd.read_csv(_INPUT_FILE).dropna(subset=['cleaned_text'])
X_raw = df['cleaned_text']
y     = df['label']

X_train_raw, X_test_raw, y_train, y_test = train_test_split(
    X_raw, y, test_size=0.2, random_state=42
)
print(f"Train: {len(X_train_raw)}  |  Test: {len(X_test_raw)}\n")

# ── Benchmark ─────────────────────────────────────────────────────────────────
results = []

for n_feat in _MAX_FEATURES_LIST:
    print(f"=== max_features={n_feat} ===")

    vec   = TfidfVectorizer(max_features=n_feat, sublinear_tf=True)
    X_all = vec.fit_transform(X_raw)

    # Cross-validation (5-fold stratificato) sull'intero dataset
    clf_cv = LinearSVC(random_state=42, max_iter=2000)
    cv_scores = cross_val_score(clf_cv, X_all, y, cv=StratifiedKFold(5, shuffle=True, random_state=42), scoring='accuracy')

    # Hold-out 80/20
    X_train = vec.transform(X_train_raw)
    X_test  = vec.transform(X_test_raw)
    clf     = LinearSVC(random_state=42, max_iter=2000)
    clf.fit(X_train, y_train)
    y_pred  = clf.predict(X_test)

    acc     = accuracy_score(y_test, y_pred)
    n_err   = int((y_test != y_pred).sum())
    report  = classification_report(y_test, y_pred, output_dict=True)

    per_class_f1 = {sport: report[sport]['f1-score'] for sport in _SPORTS}

    row = {
        'max_features':    n_feat,
        'accuracy':        acc,
        'n_errors':        n_err,
        'cv_mean':         cv_scores.mean(),
        'cv_std':          cv_scores.std(),
        'macro_f1':        report['macro avg']['f1-score'],
        'macro_precision': report['macro avg']['precision'],
        'macro_recall':    report['macro avg']['recall'],
        **{f'f1_{s}': per_class_f1[s] for s in _SPORTS},
    }
    results.append(row)

    print(f"  Accuracy hold-out : {acc*100:.4f}%  ({n_err} errori)")
    print(f"  CV 5-fold         : {cv_scores.mean()*100:.4f}% ± {cv_scores.std()*100:.4f}%")
    print(f"  Macro F1          : {report['macro avg']['f1-score']:.4f}")
    for s in _SPORTS:
        print(f"    {s:<12} F1={per_class_f1[s]:.4f}")
    print()

df_res = pd.DataFrame(results)
print(df_res[['max_features','accuracy','cv_mean','cv_std','macro_f1','n_errors']].to_string(index=False))

# ── Stile grafico ──────────────────────────────────────────────────────────────
ACCENT  = '#f97316'
ACCENT2 = '#fbbf24'
BG      = '#0d0d0d'
SURFACE = '#1a1a1a'
TEXT    = '#f5f5f5'
MUTED   = '#999999'

def apply_dark(ax, fig):
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(SURFACE)
    ax.tick_params(colors=TEXT, labelsize=9)
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)
    ax.title.set_color(ACCENT)
    for spine in ax.spines.values():
        spine.set_edgecolor('#333')
    ax.grid(True, color='#2a2a2a', linewidth=0.8)

xs = df_res['max_features'].values

# ── Grafico 1: Accuracy hold-out + CV mean ────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 4.5))
apply_dark(ax, fig)

ax.plot(xs, df_res['accuracy']*100,   marker='o', color=ACCENT,  linewidth=2, label='Hold-out accuracy')
ax.fill_between(xs,
    (df_res['cv_mean'] - df_res['cv_std'])*100,
    (df_res['cv_mean'] + df_res['cv_std'])*100,
    alpha=0.2, color=ACCENT2)
ax.plot(xs, df_res['cv_mean']*100, marker='s', color=ACCENT2, linewidth=2, linestyle='--', label='CV 5-fold mean ± std')

for _, r in df_res.iterrows():
    ax.annotate(f"{r['accuracy']*100:.2f}%",
                (r['max_features'], r['accuracy']*100),
                textcoords='offset points', xytext=(0, 8),
                ha='center', fontsize=8, color=ACCENT)

ax.set_xlabel('max_features')
ax.set_ylabel('Accuracy (%)')
ax.set_title('Accuracy vs max_features')
ax.set_xticks(xs)
ax.legend(facecolor=SURFACE, edgecolor='#333', labelcolor=TEXT, fontsize=9)
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.2f'))
plt.tight_layout()
fig.savefig(f'{_PLOTS_DIR}/1_accuracy.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"Salvato: {_PLOTS_DIR}/1_accuracy.png")

# ── Grafico 2: Precision / Recall / F1 macro ──────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 4.5))
apply_dark(ax, fig)

ax.plot(xs, df_res['macro_precision']*100, marker='o', color=ACCENT,  linewidth=2, label='Macro Precision')
ax.plot(xs, df_res['macro_recall']*100,    marker='s', color=ACCENT2, linewidth=2, label='Macro Recall')
ax.plot(xs, df_res['macro_f1']*100,        marker='^', color='#60a5fa', linewidth=2, label='Macro F1')

ax.set_xlabel('max_features')
ax.set_ylabel('Score (%)')
ax.set_title('Macro Precision / Recall / F1 vs max_features')
ax.set_xticks(xs)
ax.legend(facecolor=SURFACE, edgecolor='#333', labelcolor=TEXT, fontsize=9)
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.2f'))
plt.tight_layout()
fig.savefig(f'{_PLOTS_DIR}/2_macro_prf.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"Salvato: {_PLOTS_DIR}/2_macro_prf.png")

# ── Grafico 3: Numero errori ───────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 4))
apply_dark(ax, fig)

bars = ax.bar(xs, df_res['n_errors'], color=ACCENT, width=600, edgecolor=BG)
for bar, n in zip(bars, df_res['n_errors']):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
            str(int(n)), ha='center', va='bottom', color=TEXT, fontsize=10, fontweight='bold')

ax.set_xlabel('max_features')
ax.set_ylabel('Errori sul test set')
ax.set_title('Numero di errori (hold-out) vs max_features')
ax.set_xticks(xs)
ax.set_ylim(0, df_res['n_errors'].max() * 1.3)
plt.tight_layout()
fig.savefig(f'{_PLOTS_DIR}/3_errors.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"Salvato: {_PLOTS_DIR}/3_errors.png")

# ── Grafico 4: F1 per categoria (heatmap-style) ───────────────────────────────
f1_matrix = df_res[[f'f1_{s}' for s in _SPORTS]].values  # (n_configs, n_sports)

fig, ax = plt.subplots(figsize=(10, 4.5))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

im = ax.imshow(f1_matrix.T, aspect='auto', cmap='YlOrRd', vmin=0.90, vmax=1.00)

ax.set_xticks(range(len(xs)))
ax.set_xticklabels([str(x) for x in xs], color=TEXT, fontsize=9)
ax.set_yticks(range(len(_SPORTS)))
ax.set_yticklabels(_SPORTS, color=TEXT, fontsize=9)
ax.set_xlabel('max_features', color=TEXT)
ax.set_title('F1-score per categoria vs max_features', color=ACCENT)
ax.tick_params(colors=TEXT)
for spine in ax.spines.values():
    spine.set_visible(False)

for i in range(f1_matrix.shape[0]):
    for j in range(len(_SPORTS)):
        val = f1_matrix[i, j]
        ax.text(i, j, f"{val:.3f}", ha='center', va='center',
                fontsize=8.5, color='black' if val > 0.95 else 'white', fontweight='bold')

cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
cbar.ax.tick_params(colors=TEXT, labelsize=8)
cbar.set_label('F1-score', color=TEXT)

plt.tight_layout()
fig.savefig(f'{_PLOTS_DIR}/4_f1_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"Salvato: {_PLOTS_DIR}/4_f1_heatmap.png")

# ── Grafico 5: CV std (stabilità) ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 4))
apply_dark(ax, fig)

ax.plot(xs, df_res['cv_std']*100, marker='o', color=ACCENT2, linewidth=2)
ax.fill_between(xs, 0, df_res['cv_std']*100, alpha=0.2, color=ACCENT2)
for x, v in zip(xs, df_res['cv_std']*100):
    ax.annotate(f"{v:.4f}%", (x, v), textcoords='offset points', xytext=(0, 6),
                ha='center', fontsize=8, color=ACCENT2)

ax.set_xlabel('max_features')
ax.set_ylabel('Std deviazione CV (%)')
ax.set_title('Stabilità del modello (CV std) vs max_features')
ax.set_xticks(xs)
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.4f'))
plt.tight_layout()
fig.savefig(f'{_PLOTS_DIR}/5_cv_std.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"Salvato: {_PLOTS_DIR}/5_cv_std.png")

print(f"\nTutti i grafici salvati in '{_PLOTS_DIR}/'")
print("\nRiepilogo finale:")
print(df_res[['max_features','accuracy','n_errors','cv_mean','cv_std','macro_f1']].to_string(index=False))
