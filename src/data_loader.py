import requests
import pandas as pd
import time
import os
from datetime import datetime

_KEYS_FILE   = 'api-keys.csv'
_OUTPUT_FILE = 'data/raw/dataset_sport_master.csv'

# ── Configurazione ─────────────────────────────────────────────────────────────
# Data target: tutti gli articoli vengono estratti da questo singolo giorno.
# Ogni API key copre una pagina diversa → key 1 = pagina 1 (art. 1-10),
# key 2 = pagina 2 (art. 11-20), ecc.
TARGET_DATE_STR = "2026-04-22"

SPORTS = ['soccer', 'tennis', 'basketball', 'rugby', 'F1', 'baseball', 'golf']
URL    = "https://gnews.io/api/v4/search"

# ── Lettura API keys ───────────────────────────────────────────────────────────
try:
    keys_df  = pd.read_csv(_KEYS_FILE)
    api_keys = keys_df['apiKey'].tolist()
    accounts = keys_df['account'].tolist()
    print(f"Caricate {len(api_keys)} API key da '{_KEYS_FILE}'.\n")
except FileNotFoundError:
    print(f"ERRORE: '{_KEYS_FILE}' non trovato.")
    exit()

# ── Estrazione ─────────────────────────────────────────────────────────────────
target_date = datetime.strptime(TARGET_DATE_STR, "%Y-%m-%d")
date_from   = f"{TARGET_DATE_STR}T00:00:00Z"
date_to     = f"{TARGET_DATE_STR}T23:59:59Z"

print(f"Data target: {TARGET_DATE_STR}")
print(f"Pagine da scaricare: {len(api_keys)} (10 articoli/sport per pagina)\n")

all_articles = []

for index, api_key in enumerate(api_keys):
    page         = index + 1
    account_name = accounts[index]

    print(f"--- [KEY: {account_name}] Pagina {page} — articoli {(page-1)*10+1}–{page*10} ---")

    for sport in SPORTS:
        params = {
            'q':      sport,
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
                print(f"  -> [{sport.upper()}] {len(articles)} articoli (pagina {page})")

                for article in articles:
                    all_articles.append({
                        'label':       sport,
                        'title':       article.get('title'),
                        'description': article.get('description'),
                        'content':     article.get('content'),
                        'url':         article.get('url'),
                        'date':        article.get('publishedAt'),
                    })
            else:
                print(f"  -> ERRORE [{sport.upper()}] {response.status_code}: {response.text[:120]}")

        except requests.exceptions.RequestException as e:
            print(f"  -> ERRORE CONNESSIONE: {e}")

        time.sleep(1)

    print("-" * 50)

# ── Salvataggio con deduplicazione ─────────────────────────────────────────────
if not all_articles:
    print("\nNessun articolo estratto.")
else:
    df_new = pd.DataFrame(all_articles)
    df_new = df_new.drop_duplicates(subset=['url'])

    if os.path.isfile(_OUTPUT_FILE):
        already_seen = set(pd.read_csv(_OUTPUT_FILE, usecols=['url'])['url'])
        df_new = df_new[~df_new['url'].isin(already_seen)]

    if df_new.empty:
        print("\nNessun articolo nuovo — tutti già presenti nel dataset.")
    elif os.path.isfile(_OUTPUT_FILE):
        df_new.to_csv(_OUTPUT_FILE, mode='a', header=False, index=False, encoding='utf-8')
        print(f"\nAggiunti {len(df_new)} nuovi articoli a '{_OUTPUT_FILE}'.")
    else:
        df_new.to_csv(_OUTPUT_FILE, index=False, encoding='utf-8')
        print(f"\nCreato '{_OUTPUT_FILE}' con {len(df_new)} articoli.")

    print(f"Massimo teorico: {len(api_keys)} key × {len(SPORTS)} sport × 10 art = "
          f"{len(api_keys) * len(SPORTS) * 10} articoli/giorno")
