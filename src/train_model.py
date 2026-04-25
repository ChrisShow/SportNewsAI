import json
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report, accuracy_score

_INPUT_FILE      = 'data/processed/dataset_sport_cleaned.csv'
_MODEL_FILE      = 'models/svm_sport_classifier.joblib'
_VECTORIZER_FILE = 'models/tfidf_vectorizer.joblib'
_RESULTS_FILE    = 'models/results.json'

print("1. Caricamento del dataset pulito...")
df = pd.read_csv(_INPUT_FILE)

# Controllo di sicurezza: eliminiamo eventuali righe che, dopo la pulizia, 
# sono rimaste completamente vuote o nulle
df = df.dropna(subset=['cleaned_text'])

# Separiamo l'input (X) dall'output desiderato (y)
X_raw = df['cleaned_text']
y = df['label']

print("\n2. Avvio la vettorizzazione TF-IDF...")
# Inizializziamo il vettorizzatore. 
# max_features=5000 prende solo le 5000 parole più frequenti nel dataset, 
# filtrando gli errori di battitura o parole rarissime per alleggerire la matrice.
vectorizer = TfidfVectorizer(max_features=5000, sublinear_tf=True)

# fit_transform crea il vocabolario e converte gli articoli in vettori numerici
X = vectorizer.fit_transform(X_raw)

print(f"   Matrice creata! Dimensioni: {X.shape[0]} articoli x {X.shape[1]} parole.")

print("\n3. Suddivisione dei dati (Train/Test Split)...")
# Dividiamo i dati: l'80% serve per studiare, il 20% serve per l'esame finale
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"   Articoli di addestramento: {X_train.shape[0]}")
print(f"   Articoli di test: {X_test.shape[0]}")

print("\n4. Addestramento del Modello (Support Vector Machine)...")
model = LinearSVC(random_state=42)
# La magia avviene qui: il modello impara a collegare la matematica del TF-IDF agli sport
model.fit(X_train, y_train)

print("\n5. Valutazione del Modello sui dati di Test...")
# Chiediamo al modello di prevedere gli sport per il 20% di articoli che non ha mai visto
y_pred = model.predict(X_test)

# Calcoliamo le metriche
acc = accuracy_score(y_test, y_pred)
print(f"\n>>> ACCURATEZZA GLOBALE: {acc * 100:.2f}% <<<")

print("\n--- REPORT DI CLASSIFICAZIONE DETTAGLIATO ---")
# Questo report ti mostrerà Precisione, Recall e F1-Score per ogni singolo sport
print(classification_report(y_test, y_pred))

print("\n6. Salvataggio del modello, vectorizer e risultati...")
joblib.dump(model, _MODEL_FILE)
joblib.dump(vectorizer, _VECTORIZER_FILE)

report = classification_report(y_test, y_pred, output_dict=True)
results = {
    "accuracy": round(acc, 4),
    "n_test": len(y_test),
    "n_errors": int((y_test != y_pred).sum()),
    "per_class": {
        label: {
            "precision": round(vals["precision"], 2),
            "recall":    round(vals["recall"], 2),
            "f1-score":  round(vals["f1-score"], 2),
            "support":   int(vals["support"]),
        }
        for label, vals in report.items()
        if label not in ("accuracy", "macro avg", "weighted avg")
    }
}
with open(_RESULTS_FILE, "w") as f:
    json.dump(results, f, indent=2)

print(f"   Modello salvato in '{_MODEL_FILE}'.")
print(f"   Vectorizer salvato in '{_VECTORIZER_FILE}'.")
print(f"   Risultati salvati in '{_RESULTS_FILE}'.")