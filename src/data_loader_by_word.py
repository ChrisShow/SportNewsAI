import requests
import pandas as pd
import time
import os
from datetime import datetime, timedelta

_KEYS_FILE   = '../api-keys.csv'
_OUTPUT_FILE = '../data/raw/dataset_sport_master.csv'

# ── Configurazione utente ──────────────────────────────────────────────────────
START_DATE_STR = "2026-04-22"   # data di partenza (più recente)
MIN_DATE_STR   = "2026-01-01"   # limite inferiore: non andare oltre questa data
WORD           = "nba"        # keyword da ricercare su GNews
SPORT          = "basketball"        # label da assegnare agli articoli raccolti
PAGES_PER_KEY  = 3               # pagine per chiave API (3 × 10 = 30 articoli max/chiave)

URL = "https://gnews.io/api/v4/search"

# ── Lettura API keys ───────────────────────────────────────────────────────────
try:
    keys_df  = pd.read_csv(_KEYS_FILE)
    api_keys = keys_df['apiKey'].tolist()
    accounts = keys_df['account'].tolist()
    print(f"Caricate {len(api_keys)} API key da '{_KEYS_FILE}'.")
except FileNotFoundError:
    print(f"ERRORE: '{_KEYS_FILE}' non trovato.")
    exit()

# ── Carica URL già presenti per deduplicazione ────────────────────────────────
if os.path.isfile(_OUTPUT_FILE):
    already_seen = set(pd.read_csv(_OUTPUT_FILE, usecols=['url'])['url'].dropna())
    print(f"Articoli già nel dataset: {len(already_seen)}")
else:
    already_seen = set()

min_date = datetime.strptime(MIN_DATE_STR, "%Y-%m-%d")

# ── Raccolta ───────────────────────────────────────────────────────────────────
current_date = datetime.strptime(START_DATE_STR, "%Y-%m-%d")
current_page = 1      # prima pagina disponibile per la data corrente
all_articles = []
date_changes = 0

teorico_max = len(api_keys) * PAGES_PER_KEY * 10
print(f"\nKeyword : '{WORD}' → label: '{SPORT}'")
print(f"Da      : {START_DATE_STR}  |  Min: {MIN_DATE_STR}")
print(f"Teorico : {len(api_keys)} chiavi × {PAGES_PER_KEY} pag × 10 art = {teorico_max} articoli max\n")

for key_index, (api_key, account_name) in enumerate(zip(api_keys, accounts)):

    if current_date < min_date:
        print(f"[STOP] Raggiunta la data minima ({MIN_DATE_STR}).")
        break

    date_str  = current_date.strftime("%Y-%m-%d")
    date_from = f"{date_str}T00:00:00Z"
    date_to   = f"{date_str}T23:59:59Z"

    print(f"--- [{account_name}] {date_str} — pagine {current_page}..{current_page + PAGES_PER_KEY - 1} ---")

    zero_hit = False

    for page_offset in range(PAGES_PER_KEY):
        page = current_page + page_offset

        params = {
            'q':      WORD,
            'lang':   'en',
            'max':    10,
            'page':   page,
            'from':   date_from,
            'to':     date_to,
            'apikey': api_key,
        }

        try:
            response = requests.get(URL, params=params)

            if response.status_code == 200:
                articles = response.json().get('articles', [])
                print(f"  -> pagina {page}: {len(articles)} articoli")

                if len(articles) == 0:
                    # Nessun risultato: scala la data e resetta il cursore pagina
                    current_date -= timedelta(days=1)
                    current_page  = 1
                    date_changes += 1
                    print(f"  -> 0 articoli — nuova data: {current_date.strftime('%Y-%m-%d')}")
                    zero_hit = True
                    break

                new_count = 0
                for article in articles:
                    url = article.get('url')
                    if url and url not in already_seen:
                        all_articles.append({
                            'label':       SPORT,
                            'title':       article.get('title'),
                            'description': article.get('description'),
                            'content':     article.get('content'),
                            'url':         url,
                            'date':        article.get('publishedAt'),
                        })
                        already_seen.add(url)
                        new_count += 1

                if new_count < len(articles):
                    print(f"     ({len(articles) - new_count} duplicati scartati)")

            else:
                print(f"  -> ERRORE {response.status_code}: {response.text[:120]}")

        except requests.exceptions.RequestException as e:
            print(f"  -> ERRORE CONNESSIONE: {e}")

        time.sleep(1)

    # Se nessuna pagina di questa chiave ha restituito 0 risultati,
    # avanza il cursore in modo che la prossima chiave copra pagine diverse
    if not zero_hit:
        current_page += PAGES_PER_KEY

    print("-" * 50)

# ── Salvataggio ────────────────────────────────────────────────────────────────
print(f"\nArticoli nuovi raccolti : {len(all_articles)}")
print(f"Cambi di data           : {date_changes}")
print(f"Data finale raggiunta   : {current_date.strftime('%Y-%m-%d')}")

if all_articles:
    df_new = pd.DataFrame(all_articles).drop_duplicates(subset=['url'])

    if os.path.isfile(_OUTPUT_FILE):
        df_new.to_csv(_OUTPUT_FILE, mode='a', header=False, index=False, encoding='utf-8')
        print(f"Aggiunti {len(df_new)} articoli a '{_OUTPUT_FILE}'.")
    else:
        df_new.to_csv(_OUTPUT_FILE, index=False, encoding='utf-8')
        print(f"Creato '{_OUTPUT_FILE}' con {len(df_new)} articoli.")
else:
    print("Nessun nuovo articolo da aggiungere.")
