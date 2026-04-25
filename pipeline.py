import json
import re
import subprocess
import sys
import time

import pandas as pd

STEPS = [
    ("Raccolta dati",            "src/data_loader.py"),
    ("Preprocessing testo",      "src/preprocess_data.py"),
    ("Training del modello",     "src/train_model.py"),
    ("Esportazione web (JSON)",  "src/export_model.py"),
]

_RAW_CSV      = "data/raw/dataset_sport_master.csv"
_RESULTS_JSON = "models/results.json"
_README       = "README.md"
_INDEX_HTML   = "docs/index.html"


def run_step(name, script):
    print(f"\n{'='*60}")
    print(f"  STEP: {name}")
    print(f"  Script: {script}")
    print(f"{'='*60}\n")

    start = time.time()
    result = subprocess.run([sys.executable, script], text=True)
    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"\n[ERRORE] Lo step '{name}' ha fallito (exit code {result.returncode}).")
        print("Pipeline interrotta.")
        sys.exit(result.returncode)

    print(f"\n[OK] '{name}' completato in {elapsed:.1f}s.")


def update_readme():
    print(f"\n{'='*60}")
    print(f"  STEP: Aggiornamento README")
    print(f"{'='*60}\n")

    # --- Carica dati dataset ---
    df = pd.read_csv(_RAW_CSV)
    total = len(df)
    date_min = df["date"].min()[:10]
    date_max = df["date"].max()[:10]
    date_range = f"{date_min} → {date_max}"
    counts = df["label"].value_counts()
    min_count, max_count = counts.min(), counts.max()
    distribuzione = f"bilanciata (~{min_count}–{max_count} per categoria)"

    # --- Carica risultati modello ---
    with open(_RESULTS_JSON) as f:
        res = json.load(f)
    accuracy_pct = res["accuracy"] * 100
    n_test   = res["n_test"]
    n_errors = res["n_errors"]

    # --- Leggi README ---
    with open(_README, encoding="utf-8") as f:
        readme = f.read()

    # Tabella dataset (parametri generali)
    new_dataset_table = (
        "| Parametro | Valore |\n"
        "|---|---|\n"
        f"| Articoli totali | {total} |\n"
        f"| Periodo coperto | {date_range} |\n"
        f"| Distribuzione label | {distribuzione} |\n"
        "| Lingua | Inglese |"
    )
    readme = re.sub(
        r"\| Parametro \| Valore \|.*?\| Lingua \| Inglese \|",
        new_dataset_table,
        readme,
        flags=re.DOTALL,
    )

    # Tabella distribuzione per sport
    sport_rows = "\n".join(
        f"| {sport} | {count} |" for sport, count in counts.items()
    )
    new_sport_table = "| Sport | Articoli |\n|---|---|\n" + sport_rows
    readme = re.sub(
        r"\| Sport \| Articoli \|.*?(?=\n---)",
        new_sport_table,
        readme,
        flags=re.DOTALL,
    )

    # Riga accuracy (pattern include la parte tra parentesi per evitare duplicazioni)
    readme = re.sub(
        r"\*\*Accuracy complessiva:.*?errori\)",
        f"**Accuracy complessiva: {accuracy_pct:.2f}%** ({n_test} articoli di test, {n_errors} errori)",
        readme,
    )

    # Tabella classificazione per classe
    header = "| Sport | Precision | Recall | F1-score | Support |\n|---|---|---|---|---|\n"
    class_rows = "\n".join(
        f"| {label} | {v['precision']:.2f} | {v['recall']:.2f} | {v['f1-score']:.2f} | {v['support']} |"
        for label, v in sorted(res["per_class"].items())
    )
    new_class_table = header + class_rows
    readme = re.sub(
        r"\| Sport \| Precision \| Recall \| F1-score \| Support \|.*?(?=\n---)",
        new_class_table,
        readme,
        flags=re.DOTALL,
    )

    with open(_README, "w", encoding="utf-8") as f:
        f.write(readme)

    # Aggiorna accuracy nell'index.html
    with open(_INDEX_HTML, encoding="utf-8") as f:
        html = f.read()
    html = re.sub(
        r"Accuratezza: [\d.]+%",
        f"Accuratezza: {accuracy_pct:.2f}%",
        html,
    )
    with open(_INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"   Articoli totali: {total}")
    print(f"   Periodo: {date_range}")
    print(f"   Accuracy: {accuracy_pct:.2f}% ({n_test} test, {n_errors} errori)")
    print(f"\n[OK] README e index.html aggiornati.")


if __name__ == "__main__":
    print("\nAVVIO PIPELINE SPORTNEWSAI")
    pipeline_start = time.time()

    for name, script in STEPS:
        run_step(name, script)

    update_readme()

    total_time = time.time() - pipeline_start
    print(f"\n{'='*60}")
    print(f"  PIPELINE COMPLETATA in {total_time:.1f}s")
    print(f"{'='*60}\n")
