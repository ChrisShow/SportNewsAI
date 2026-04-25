import pandas as pd
import re
import nltk
from nltk.corpus import stopwords

_INPUT_FILE  = 'data/raw/dataset_sport_master.csv'
_OUTPUT_FILE = 'data/processed/dataset_sport_cleaned.csv'

# Scarichiamo la lista delle stop-words inglesi la prima volta che eseguiamo il codice
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

def clean_text(text):
    # 1. Controllo di sicurezza: se la cella è vuota, restituisci una stringa vuota
    if type(text) != str:
        return ""
    
    # 2. Tutto in minuscolo (Lowercase)
    text = text.lower()
    
    # 3. Rimuoviamo punteggiatura, caratteri speciali e numeri. 
    # Teniamo SOLO le lettere dell'alfabeto (a-z) e gli spazi.
    text = re.sub(r'[^a-z\s]', '', text)
    
    # 4. Rimuoviamo le stop-words
    words = text.split() # Dividiamo la frase in singole parole
    cleaned_words = [w for w in words if w not in stop_words and len(w) > 1] # Filtriamo
    
    # 5. Riuniamo le parole in una stringa pulita
    return " ".join(cleaned_words)

# --- ESECUZIONE SUL DATASET ---

print("Caricamento del dataset...")
df = pd.read_csv(_INPUT_FILE)

print("Inizio la pulizia del testo (potrebbe volerci qualche secondo)...")
# full_text = title + description + content; concateniamo title una seconda volta
# per dare maggior peso al titolo nella rappresentazione TF-IDF
full_text = (
    df['title'].fillna('') + " " +
    df['description'].fillna('') + " " +
    df['content'].fillna('')
)
source_text = df['title'].fillna('') + " " + full_text
df['cleaned_text'] = source_text.apply(clean_text)

# Salviamo solo le colonne necessarie al training
df[['label', 'url', 'date', 'cleaned_text']].to_csv(_OUTPUT_FILE, index=False)

print(f"Pulizia completata! Dataset salvato in '{_OUTPUT_FILE}'.")

# Stampiamo un esempio per vedere la differenza
print("\n--- ESEMPIO DI PULIZIA ---")
print("PRIMA: ", source_text.iloc[0][:150], "...")
print("DOPO:  ", df['cleaned_text'].iloc[0][:150], "...")