# SportNewsAI — Classificazione Automatica di Articoli Sportivi

Progetto sviluppato nell'ambito del corso **Fisica dei sistemi neurali e intelligenza artificiale**.  
Obiettivo: classificazione multi-classe di articoli giornalistici sportivi in 7 categorie mediante tecniche di machine learning supervisionato.

---

## Categorie di classificazione

| Label | Sport |
|---|---|
| `soccer` | Calcio |
| `tennis` | Tennis |
| `basketball` | Pallacanestro |
| `rugby` | Rugby |
| `F1` | Formula 1 |
| `baseball` | Baseball |
| `golf` | Golf |

---

## Pipeline

```
GNews API → data_loader.py → dataset_sport_master.csv
                                        ↓
                              preprocess_data.py → dataset_sport_cleaned.csv
                                                            ↓
                                                   train_model.py → modello + metriche
                                                            ↓
                                                   export_model.py → model_data.json
```

Esecuzione dell'intera pipeline:

```bash
python pipeline.py
```

### 1. Raccolta dati — `src/data_loader.py`

- **Sorgente**: API REST [GNews.io](https://gnews.io/) (piano gratuito)
- **Metodo**: query per ciascuna categoria (`q='soccer'`, `q='tennis'`, ecc.) con rotazione su 9 chiavi API, una per giorno
- **Output**: `data/raw/dataset_sport_master.csv` — colonne `label, title, description, content, url, date`

**Limitazione**: il piano gratuito di GNews.io tronca il campo `content` a circa 253 caratteri. Il modello opera prevalentemente su titolo e descrizione.

### 2. Preprocessing — `src/preprocess_data.py`

- Conversione in minuscolo
- Rimozione di caratteri non alfabetici (`re.sub(r'[^a-z\s]', '', text)`)
- Eliminazione delle stopwords inglesi (corpus NLTK `stopwords.words('english')`)
- **Output**: `data/processed/dataset_sport_cleaned.csv` — aggiunge la colonna `cleaned_text`

### 3. Addestramento — `src/train_model.py`

- **Vettorizzazione**: `TfidfVectorizer` con `max_features=5000`
- **Modello**: `LinearSVC` (scikit-learn), classificazione one-vs-rest
- **Partizione**: 80% training / 20% test, `random_state=42`
- **Output**: modello (`models/svm_sport_classifier.joblib`), vectorizer (`models/tfidf_vectorizer.joblib`), metriche (`models/results.json`)

### 4. Esportazione web — `src/export_model.py`

Esporta vocabolario, pesi IDF e coefficienti LinearSVC in `docs/model_data.json` per l'inferenza client-side in JavaScript. Calcola il threshold di confidenza come 5° percentile dei punteggi massimi della decision function sul test set.

---

## Dataset

| Parametro | Valore |
|---|---|
| Articoli totali | 3617 |
| Periodo coperto | 2026-03-16 → 2026-04-22 |
| Distribuzione label | bilanciata (~413–743 per categoria) |
| Lingua | Inglese |

Distribuzione per categoria:

| Sport | Articoli |
|---|---|
| basketball | 743 |
| golf | 525 |
| soccer | 524 |
| tennis | 524 |
| baseball | 467 |
| rugby | 421 |
| F1 | 413 |
---

## Risultati

**Accuracy complessiva: 97.93%** (724 articoli di test, 15 errori)

| Sport | Precision | Recall | F1-score | Support |
|---|---|---|---|---|
| F1 | 0.98 | 0.98 | 0.98 | 90 |
| baseball | 0.95 | 0.98 | 0.96 | 93 |
| basketball | 0.98 | 0.97 | 0.98 | 152 |
| golf | 0.99 | 1.00 | 1.00 | 107 |
| rugby | 1.00 | 1.00 | 1.00 | 90 |
| soccer | 0.98 | 0.94 | 0.96 | 89 |
| tennis | 0.98 | 0.98 | 0.98 | 103 |
---

## Scelte progettuali

### LinearSVC
`LinearSVC` opera efficacemente in spazi ad alta dimensionalità quali le rappresentazioni TF-IDF. Garantisce tempi di addestramento ridotti, interpretabilità dei pesi e prestazioni competitive rispetto a modelli più complessi per task di classificazione testuale.

### TF-IDF
La rappresentazione TF-IDF è consolidata per la classificazione di testo supervisionata. Quantifica il peso relativo dei termini senza richiedere modelli pre-addestrati. Per articoli sportivi, il vocabolario specializzato (atleti, squadre, terminologia tecnica) costituisce un segnale discriminante sufficiente.

### Numero di feature (5000)
Il limite a 5000 feature bilancia copertura del vocabolario rilevante e contenimento della dimensionalità, riducendo il rischio di overfitting su un dataset di circa 3600 campioni.

### Scelta delle 7 categorie
Le categorie selezionate presentano terminologie notevolmente distinte, favorendo la separabilità lineare. Calcio e rugby rappresentano il caso più critico per prossimità semantica.

### Sorgente dati (GNews.io)
Non esistono dataset pubblici etichettati per le 7 categorie specifiche considerate. GNews.io fornisce un'API REST con filtraggio per keyword, che consente la costruzione automatica di un dataset etichettato tramite la categoria della query.

---

## Tecnologie

| Libreria | Versione | Utilizzo |
|---|---|---|
| `pandas` | 3.0.2 | Gestione e manipolazione del dataset |
| `scikit-learn` | 1.8.0 | TF-IDF, LinearSVC, metriche di valutazione |
| `nltk` | 3.9.4 | Rimozione stopwords |
| `requests` | 2.33.1 | Chiamate HTTP all'API GNews |
| `joblib` | — | Serializzazione del modello e del vectorizer |
| `numpy` | 2.4.4 | Dipendenza di scikit-learn |

**Python**: 3.11.9

---

## Limitazioni

1. **Troncamento del contenuto**: il piano gratuito di GNews.io restituisce il campo `content` parziale (~253 caratteri su ~3300). La classificazione si basa prevalentemente su titolo e descrizione.
2. **Label leakage implicito**: le query API contengono la keyword dello sport, che compare nel testo della quasi totalità degli articoli. Ciò semplifica il task rispetto a uno scenario reale con articoli non etichettati a priori.
3. **Assenza di confronto con modelli neurali**: l'approccio adottato è ML classico (SVM + TF-IDF). Un confronto con modelli transformer (es. BERT fine-tuning) potrebbe evidenziare differenze di prestazione su testi semanticamente ambigui.

---

## Struttura del progetto

```
SportNewsAI/
├── README.md
├── requirements.txt
├── pipeline.py                          # orchestrazione dell'intera pipeline
├── api-keys.csv                         # credenziali GNews (non versionato)
├── src/
│   ├── data_loader.py                   # raccolta dati via GNews API
│   ├── preprocess_data.py               # normalizzazione e pulizia del testo
│   ├── train_model.py                   # addestramento e valutazione del modello
│   └── export_model.py                  # esportazione pesi per inferenza web
├── data/                                # non versionato
│   ├── raw/
│   │   └── dataset_sport_master.csv     # dataset grezzo (3617 articoli)
│   └── processed/
│       └── dataset_sport_cleaned.csv    # dataset preprocessato
├── models/                              # non versionato
│   ├── svm_sport_classifier.joblib
│   ├── tfidf_vectorizer.joblib
│   └── results.json
└── docs/                                # pagina web (GitHub Pages)
    ├── index.html
    ├── classifier.js
    └── model_data.json
```
