"""
Genera SportNewsAI.pptx — 10 slide, sfondo bianco, testo pulito.
Eseguire dalla root del progetto:
    venv\Scripts\python.exe src/make_pptx.py
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import copy

# ── Costanti layout ────────────────────────────────────────────────────────────
W = Inches(13.33)
H = Inches(7.5)
MARGIN_L = Inches(0.7)
MARGIN_T = Inches(0.55)
CONTENT_W = Inches(11.93)
CONTENT_H = Inches(6.3)

BLACK  = RGBColor(0x1a, 0x1a, 0x1a)
GRAY   = RGBColor(0x55, 0x55, 0x55)
ACCENT = RGBColor(0x1F, 0x4E, 0x79)   # blu scuro
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
LTGRAY = RGBColor(0xF2, 0xF2, 0xF2)

# ── Helpers ────────────────────────────────────────────────────────────────────
def new_slide(prs):
    blank = prs.slide_layouts[6]  # layout completamente vuoto
    return prs.slides.add_slide(blank)

def add_textbox(slide, text, left, top, width, height,
                size=18, bold=False, color=BLACK, align=PP_ALIGN.LEFT,
                wrap=True, italic=False):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return txBox

def add_title(slide, title, subtitle=None):
    add_textbox(slide, title,
                MARGIN_L, Inches(0.3), CONTENT_W, Inches(0.7),
                size=28, bold=True, color=ACCENT)
    if subtitle:
        add_textbox(slide, subtitle,
                    MARGIN_L, Inches(0.95), CONTENT_W, Inches(0.45),
                    size=13, color=GRAY, italic=True)

def add_hline(slide, top):
    from pptx.util import Pt as UPt
    line = slide.shapes.add_connector(1, MARGIN_L, top, MARGIN_L + CONTENT_W, top)
    line.line.color.rgb = ACCENT
    line.line.width = UPt(1.2)

def bullet_tf(tf, items, size=14, indent=False):
    """Aggiunge bullet points al text frame (sovrascrive il primo paragrafo)."""
    from pptx.oxml.ns import qn
    from lxml import etree
    tf.clear()
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        run = p.add_run()
        run.text = ("    • " if indent else "• ") + item
        run.font.size = Pt(size)
        run.font.color.rgb = BLACK

def add_table(slide, headers, rows, left, top, width, height,
              header_bg=ACCENT, row_alt=LTGRAY):
    from pptx.util import Pt
    cols = len(headers)
    n_rows = len(rows) + 1
    tbl = slide.shapes.add_table(n_rows, cols, left, top, width, height).table

    col_w = width // cols
    for i in range(cols):
        tbl.columns[i].width = col_w

    # header
    for j, h in enumerate(headers):
        cell = tbl.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = header_bg
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = h
        run.font.bold = True
        run.font.size = Pt(11)
        run.font.color.rgb = WHITE

    # rows
    for i, row in enumerate(rows):
        bg = row_alt if i % 2 == 1 else WHITE
        for j, val in enumerate(row):
            cell = tbl.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            run = p.add_run()
            run.text = str(val)
            run.font.size = Pt(11)
            run.font.color.rgb = BLACK
    return tbl

def add_image(slide, path, left, top, width=None, height=None):
    pic = slide.shapes.add_picture(path, left, top, width=width, height=height)
    return pic

# ── Presentazione ──────────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width  = W
prs.slide_height = H

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — Cover
# ═══════════════════════════════════════════════════════════════════════════════
sl = new_slide(prs)

add_textbox(sl, "SportNewsAI",
            MARGIN_L, Inches(1.8), CONTENT_W, Inches(1.1),
            size=44, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)
add_textbox(sl, "Classificazione automatica di articoli sportivi",
            MARGIN_L, Inches(2.85), CONTENT_W, Inches(0.6),
            size=20, color=GRAY, align=PP_ALIGN.CENTER, italic=True)
add_hline(sl, Inches(3.65))
add_textbox(sl, "TF-IDF  ·  LinearSVC  ·  7 categorie  ·  Accuracy 97.93%",
            MARGIN_L, Inches(3.8), CONTENT_W, Inches(0.5),
            size=15, color=BLACK, align=PP_ALIGN.CENTER)
add_textbox(sl, "Corso: Fisica dei sistemi neurali e intelligenza artificiale  —  A.A. 2024/25",
            MARGIN_L, Inches(4.5), CONTENT_W, Inches(0.45),
            size=12, color=GRAY, align=PP_ALIGN.CENTER)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — Problema e obiettivo
# ═══════════════════════════════════════════════════════════════════════════════
sl = new_slide(prs)
add_title(sl, "Problema e obiettivo")
add_hline(sl, Inches(1.05))

add_textbox(sl, "Dato un articolo giornalistico sportivo in lingua inglese, assegnarlo automaticamente a una delle 7 categorie senza supervisione umana.",
            MARGIN_L, Inches(1.15), CONTENT_W, Inches(0.65), size=14)

add_textbox(sl, "Categorie",
            MARGIN_L, Inches(1.9), Inches(3), Inches(0.4), size=13, bold=True, color=ACCENT)

cats = [
    ("⚽", "Calcio (soccer)"),
    ("🎾", "Tennis"),
    ("🏀", "Basketball"),
    ("🏉", "Rugby"),
    ("🏎️", "Formula 1"),
    ("⚾", "Baseball"),
    ("⛳", "Golf"),
]
for i, (emoji, label) in enumerate(cats):
    col = i % 4
    row = i // 4
    add_textbox(sl, f"{emoji}  {label}",
                MARGIN_L + Inches(col * 3.0), Inches(2.35 + row * 0.42),
                Inches(2.9), Inches(0.4), size=13)

add_textbox(sl, "Perché è un problema ben posto",
            MARGIN_L, Inches(3.3), CONTENT_W, Inches(0.4), size=13, bold=True, color=ACCENT)

tb = sl.shapes.add_textbox(MARGIN_L, Inches(3.7), CONTENT_W, Inches(2.2))
bullet_tf(tb.text_frame, [
    "Vocabolario altamente specializzato per sport: atleti, squadre, terminologia tecnica",
    "Separabilità semantica elevata → spazio TF-IDF quasi linearmente separabile",
    "7 classi ben definite con distribuzione bilanciata (~413–743 articoli per categoria)",
    "Deployment statico su GitHub Pages: vincolo che esclude modelli neurali pesanti",
], size=13)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — Dataset
# ═══════════════════════════════════════════════════════════════════════════════
sl = new_slide(prs)
add_title(sl, "Dataset", "Costruzione automatica tramite GNews.io API")
add_hline(sl, Inches(1.05))

add_textbox(sl, "Raccolta dati",
            MARGIN_L, Inches(1.12), Inches(5), Inches(0.4), size=13, bold=True, color=ACCENT)
tb = sl.shapes.add_textbox(MARGIN_L, Inches(1.52), Inches(5.6), Inches(1.5))
bullet_tf(tb.text_frame, [
    "API REST GNews.io — piano gratuito: 10 articoli/richiesta",
    "9 chiavi API × paginazione: fino a 90 articoli/sport/giorno",
    "Query per keyword (soccer, tennis, F1 …) → label automatica",
    "Deduplicazione per URL, accumulo su più giorni",
], size=13)

add_textbox(sl, "Statistiche finali",
            MARGIN_L, Inches(3.1), Inches(5), Inches(0.4), size=13, bold=True, color=ACCENT)
add_table(sl,
    ["Parametro", "Valore"],
    [
        ["Articoli totali",   "3617"],
        ["Periodo coperto",   "2026-03-16 → 2026-04-22"],
        ["Lingua",            "Inglese"],
        ["Distribuzione",     "413–743 per categoria"],
    ],
    MARGIN_L, Inches(3.5), Inches(5.5), Inches(1.7)
)

add_image(sl, "colab/distribuzione_articoli.png",
          Inches(6.6), Inches(1.1), width=Inches(6.4))

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — Preprocessing
# ═══════════════════════════════════════════════════════════════════════════════
sl = new_slide(prs)
add_title(sl, "Preprocessing del testo")
add_hline(sl, Inches(1.05))

add_textbox(sl, "Pipeline di normalizzazione",
            MARGIN_L, Inches(1.12), CONTENT_W, Inches(0.4), size=13, bold=True, color=ACCENT)
tb = sl.shapes.add_textbox(MARGIN_L, Inches(1.52), Inches(6), Inches(1.4))
bullet_tf(tb.text_frame, [
    "Lowercasing — neutralizza variazioni ortografiche (FIFA → fifa)",
    "Rimozione caratteri non alfabetici — elimina numeri, punteggiatura, URL",
    "Stopwords NLTK inglese (179 parole) + filtro len > 1",
], size=13)

add_textbox(sl, "Testo sorgente — doppio peso al titolo",
            MARGIN_L, Inches(2.6), CONTENT_W, Inches(0.4), size=13, bold=True, color=ACCENT)
add_textbox(sl, "source = title  +  full_text      dove      full_text = title + description + content",
            MARGIN_L, Inches(3.0), CONTENT_W, Inches(0.45), size=13, color=GRAY)
add_textbox(sl, "Il titolo compare due volte: è il campo più informativo e l'unico non troncato dall'API (content troncato a ~253 caratteri).",
            MARGIN_L, Inches(3.45), CONTENT_W, Inches(0.5), size=12, color=GRAY, italic=True)

add_textbox(sl, "Parole più discriminanti per categoria",
            MARGIN_L, Inches(4.0), CONTENT_W, Inches(0.4), size=13, bold=True, color=ACCENT)
add_image(sl, "colab/parole_discriminanti.png",
          MARGIN_L, Inches(4.4), width=Inches(11.93))

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — TF-IDF
# ═══════════════════════════════════════════════════════════════════════════════
sl = new_slide(prs)
add_title(sl, "Rappresentazione TF-IDF")
add_hline(sl, Inches(1.05))

add_textbox(sl, "Formula",
            MARGIN_L, Inches(1.12), CONTENT_W, Inches(0.4), size=13, bold=True, color=ACCENT)
add_textbox(sl, "TF-IDF(t, d)  =  TF(t,d)  ×  IDF(t)",
            MARGIN_L, Inches(1.5), CONTENT_W, Inches(0.45), size=15, color=BLACK)
add_textbox(sl, "TF con smorzamento log:   TF_sub(t,d) = 1 + log(count(t,d))   →   robustezza a testi di lunghezza variabile",
            MARGIN_L, Inches(1.95), CONTENT_W, Inches(0.45), size=12, color=GRAY)
add_textbox(sl, "IDF con Laplace smoothing:   IDF(t) = log((1+N)/(1+df(t))) + 1   →   per N=3617, termine unico: IDF ≈ 8.50",
            MARGIN_L, Inches(2.35), CONTENT_W, Inches(0.45), size=12, color=GRAY)

add_textbox(sl, "Parametri del vettorizzatore",
            MARGIN_L, Inches(2.9), CONTENT_W, Inches(0.4), size=13, bold=True, color=ACCENT)
add_table(sl,
    ["Parametro", "Valore", "Motivazione"],
    [
        ["max_features",    "5000",  "Saturazione sperimentale: accuracy identica fino a 10 000"],
        ["sublinear_tf",    "True",  "Evita che articoli lunghi dominino il vettore"],
        ["Normalizzazione", "L2",    "Vettori unitari, invarianza alla lunghezza del documento"],
    ],
    MARGIN_L, Inches(3.35), Inches(11.93), Inches(1.5)
)

add_textbox(sl, "Legge di Zipf — giustificazione teorica di max_features=5000",
            MARGIN_L, Inches(4.95), CONTENT_W, Inches(0.4), size=13, bold=True, color=ACCENT)
add_textbox(sl, "La frequenza dell'i-esimo termine segue freq ∝ 1/i: le prime K parole coprono quasi tutta l'informazione utile. Oltre 5000, le feature aggiuntive sono termini rari con IDF ad alta varianza che non generalizzano.",
            MARGIN_L, Inches(5.35), CONTENT_W, Inches(0.65), size=12, color=GRAY)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — LinearSVC
# ═══════════════════════════════════════════════════════════════════════════════
sl = new_slide(prs)
add_title(sl, "Modello — LinearSVC")
add_hline(sl, Inches(1.05))

add_textbox(sl, "Problema di ottimizzazione (hinge loss + margine massimo)",
            MARGIN_L, Inches(1.12), CONTENT_W, Inches(0.4), size=13, bold=True, color=ACCENT)
add_textbox(sl, "min  ½‖w‖²  +  C · Σ max(0, 1 − yᵢ(w·xᵢ + b))",
            MARGIN_L, Inches(1.5), CONTENT_W, Inches(0.5), size=15, color=BLACK)
add_textbox(sl, "½‖w‖² → margine massimo     |     hinge loss → penalizza misclassificazioni proporzionalmente alla distanza dall'iperpiano",
            MARGIN_L, Inches(1.97), CONTENT_W, Inches(0.45), size=12, color=GRAY)

add_textbox(sl, "Classificazione multi-classe: one-vs-rest",
            MARGIN_L, Inches(2.6), CONTENT_W, Inches(0.4), size=13, bold=True, color=ACCENT)
add_textbox(sl, "Per ogni categoria k si addestra un classificatore binario  fₖ(x) = wₖ·x + bₖ\nLa classe assegnata è quella con il punteggio massimo:  ŷ = argmax_k fₖ(x)",
            MARGIN_L, Inches(2.98), CONTENT_W, Inches(0.65), size=13, color=BLACK)

add_textbox(sl, "Perché kernel lineare è sufficiente — Teorema di Cover (1965)",
            MARGIN_L, Inches(3.8), CONTENT_W, Inches(0.4), size=13, bold=True, color=ACCENT)
add_textbox(sl, "La probabilità di separabilità lineare cresce con la dimensione d e decresce con N.\nNel progetto: d = 5000 feature TF-IDF, N = 2893 campioni di training  →  d > N  →  separabilità quasi certa.\nKernel non lineari aumenterebbero la capacità espressiva rischiando overfitting.",
            MARGIN_L, Inches(4.2), CONTENT_W, Inches(0.85), size=13, color=BLACK)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 7 — Calibrazione
# ═══════════════════════════════════════════════════════════════════════════════
sl = new_slide(prs)
add_title(sl, "Calibrazione della confidenza")
add_hline(sl, Inches(1.05))

add_textbox(sl, "Problema: LinearSVC produce score grezzi (decision function), non probabilità calibrate.",
            MARGIN_L, Inches(1.12), CONTENT_W, Inches(0.45), size=13)

add_textbox(sl, "Temperature Scaling",
            MARGIN_L, Inches(1.65), CONTENT_W, Inches(0.4), size=13, bold=True, color=ACCENT)
add_textbox(sl, "pₖ(x; T) = exp(fₖ(x)/T) / Σⱼ exp(fⱼ(x)/T)\n\nT* ottimizzato minimizzando la cross-entropy sul validation set  →  T* = 0.1549",
            MARGIN_L, Inches(2.05), CONTENT_W, Inches(0.8), size=13, color=BLACK)

add_textbox(sl, "Threshold adattivo per classe",
            MARGIN_L, Inches(3.0), CONTENT_W, Inches(0.4), size=13, bold=True, color=ACCENT)
add_textbox(sl, "pₖ = 0.5 + (0.5 · f1_norm,k + 0.5 · n_norm,k) × 1.5",
            MARGIN_L, Inches(3.4), CONTENT_W, Inches(0.45), size=13, color=BLACK)
add_textbox(sl, "Classi con F1 più alto e maggior supporto ricevono una soglia più alta → il modello è più conservativo dove è più affidabile.",
            MARGIN_L, Inches(3.85), CONTENT_W, Inches(0.5), size=12, color=GRAY, italic=True)

add_textbox(sl, "Deployment client-side (JavaScript)",
            MARGIN_L, Inches(4.45), CONTENT_W, Inches(0.4), size=13, bold=True, color=ACCENT)
tb = sl.shapes.add_textbox(MARGIN_L, Inches(4.85), CONTENT_W, Inches(1.5))
bullet_tf(tb.text_frame, [
    "Parametri esportati in model_data.json (364 KB): vocabolario, pesi IDF, coefficienti LinearSVC, T*, soglie",
    "Pipeline replicata in JavaScript vanilla — nessun server backend, nessuna dipendenza esterna",
    "Deploy su GitHub Pages: completamente gratuito e statico",
], size=13)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 8 — Risultati
# ═══════════════════════════════════════════════════════════════════════════════
sl = new_slide(prs)
add_title(sl, "Risultati sperimentali")
add_hline(sl, Inches(1.05))

add_textbox(sl, "Accuracy globale: 97.93%  —  724 articoli di test, 15 errori",
            MARGIN_L, Inches(1.12), CONTENT_W, Inches(0.45), size=16, bold=True, color=ACCENT)

add_table(sl,
    ["Sport", "Precision", "Recall", "F1-score", "Support"],
    [
        ["F1",         "0.98", "0.98", "0.98", "90"],
        ["Baseball",   "0.95", "0.98", "0.96", "93"],
        ["Basketball", "0.98", "0.97", "0.98", "152"],
        ["Golf",       "0.99", "1.00", "1.00", "107"],
        ["Rugby",      "1.00", "1.00", "1.00", "90"],
        ["Soccer",     "0.98", "0.94", "0.96", "89"],
        ["Tennis",     "0.98", "0.98", "0.98", "103"],
    ],
    MARGIN_L, Inches(1.65), Inches(5.4), Inches(2.65)
)

add_image(sl, "colab/precision_recall_f1score.png",
          Inches(6.1), Inches(1.1), width=Inches(6.9))

add_textbox(sl, "Rugby e golf raggiungono F1=1.00 — vocabolario tecnico esclusivo.\nSoccer ha il recall più basso (0.94): overlap lessicale con rugby e altri sport di squadra.",
            MARGIN_L, Inches(4.4), CONTENT_W, Inches(0.7), size=12, color=GRAY, italic=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 9 — Matrice di confusione
# ═══════════════════════════════════════════════════════════════════════════════
sl = new_slide(prs)
add_title(sl, "Analisi degli errori — Matrice di confusione")
add_hline(sl, Inches(1.05))

add_image(sl, "colab/matrice_confusione.png",
          Inches(2.2), Inches(1.15), width=Inches(8.9))

add_textbox(sl, "15 errori su 724 campioni. Soccer e baseball presentano la maggiore confusione con sport semanticamente adiacenti (rugby, cricket).",
            MARGIN_L, Inches(6.6), CONTENT_W, Inches(0.6), size=12, color=GRAY, italic=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 10 — Conclusioni
# ═══════════════════════════════════════════════════════════════════════════════
sl = new_slide(prs)
add_title(sl, "Conclusioni e sviluppi futuri")
add_hline(sl, Inches(1.05))

add_textbox(sl, "Risultati",
            MARGIN_L, Inches(1.12), CONTENT_W, Inches(0.4), size=13, bold=True, color=ACCENT)
tb = sl.shapes.add_textbox(MARGIN_L, Inches(1.52), Inches(5.8), Inches(1.6))
bullet_tf(tb.text_frame, [
    "Accuracy 97.93% su 3617 articoli, 7 categorie",
    "TF-IDF + LinearSVC: approccio classico competitivo per vocabolario specializzato",
    "Modello deployato interamente nel browser (GitHub Pages, zero costi)",
    "Benchmark su max_features 5000–10000: plateau — 5000 è già ottimale",
], size=13)

add_textbox(sl, "Limitazioni",
            MARGIN_L, Inches(3.25), CONTENT_W, Inches(0.4), size=13, bold=True, color=ACCENT)
tb = sl.shapes.add_textbox(MARGIN_L, Inches(3.65), Inches(5.8), Inches(1.2))
bullet_tf(tb.text_frame, [
    "Label leakage implicito: la keyword sportiva compare nel testo degli articoli",
    "Content troncato a ~253 caratteri dal piano gratuito GNews",
    "Solo 7 sport, solo inglese",
], size=13)

add_textbox(sl, "Sviluppi futuri",
            Inches(7.0), Inches(1.12), Inches(5.8), Inches(0.4), size=13, bold=True, color=ACCENT)
tb = sl.shapes.add_textbox(Inches(7.0), Inches(1.52), Inches(5.9), Inches(1.6))
bullet_tf(tb.text_frame, [
    "BERT/RoBERTa fine-tuning per testi semanticamente ambigui",
    "Espansione a più sport e più lingue",
    "Rimozione del leakage: filtraggio keyword pre-classificazione",
    "API REST live per classificazione in tempo reale",
], size=13)

add_hline(sl, Inches(4.95))
add_textbox(sl, "Demo live: chrisshow.github.io/SportNewsAI   |   Codice: github.com/ChrisShow/SportNewsAI",
            MARGIN_L, Inches(5.05), CONTENT_W, Inches(0.45), size=12, color=ACCENT, align=PP_ALIGN.CENTER)

# ── Salvataggio ────────────────────────────────────────────────────────────────
out = "SportNewsAI.pptx"
prs.save(out)
print(f"Salvato: {out}")
