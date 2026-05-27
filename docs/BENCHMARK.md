# Benchmark-Dokumentation

SpamGuard enthält zwei Benchmark-Tools, um lokale LLM-Modelle miteinander zu vergleichen und das beste für deinen konkreten Einsatz zu finden.

---

## Überblick: Zwei Benchmark-Tools

| | `spam_benchmark.py` | `real_benchmark.py` |
|---|---|---|
| **Befehl** | `make benchmark` | `make benchmark-real` |
| **Test-Daten** | 50 synthetische englische Mails | Deine echten Training-Mails |
| **Zweck** | Schneller Überblick, Modell-Erstcheck | Aussagekräftiger Praxistest |
| **Bayesian-Hint** | Nein | Ja (wie in Produktion) |
| **Prompt-Optimierung** | Nein | Ja (`--label`) |
| **Ergebnis-Dateien** | `model_scores.csv`, `detailed_results.csv` | `real_scores_<ts>.csv`, `real_details_<ts>.csv` |

**Empfehlung:** Starte mit `make benchmark` für einen schnellen Überblick. Nutze `make benchmark-real` für die endgültige Entscheidung und Prompt-Optimierung — er testet mit deinen eigenen deutschen Spam-Mails und spiegelt den Produktionseinsatz realistisch wider.

---

## Voraussetzungen

```bash
# 1. Ollama muss laufen
ollama serve

# 2. Mindestens ein Modell installiert haben
ollama pull gemma4:e4b     # Empfehlung: schnell + gut
ollama pull ministral-3:14b  # Empfehlung: präzise + robust

# 3. Für Real-Benchmark: trainiertes Bayesian-Modell
make train   # braucht data/training/{spam,ham}/*.eml
```

---

## 1. Synthetischer Benchmark (`make benchmark`)

Testet Modelle anhand von 50 fest definierten englischen Test-Mails aus `benchmark/test_emails.yaml`. Nützlich als schneller Erstcheck oder um Modelle zu vergleichen, für die noch keine eigenen Training-Daten vorhanden sind.

### Starten

```bash
# Interaktiv — wählt Modell aus Liste
make benchmark

# Schnelltest mit nur 5 Mails
make benchmark-quick

# Direkt mit Modellname
.venv/bin/python scripts/benchmark/spam_benchmark.py --model gemma3:12b
```

### Score-Berechnung

```
Score (0–100) = Genauigkeit% × 0.9 + Speed-Score × 0.1

Speed-Score = min(10, TPS / 100 × 10)   (TPS = Tokens pro Sekunde)
```

Genauigkeit dominiert mit 90% Gewicht. Geschwindigkeit (TPS) hat 10% Einfluss, gedeckelt bei 100 TPS = 10 Punkte.

### Reasoning-Erkennung

Das Tool erkennt automatisch Modelle mit Reasoning (z.B. `deepseek-r1`, `qwen3`):
- **Thinking: ON** — Mit Chain-of-Thought (langsamer, teils ungenauer bei einfachen Aufgaben)
- **Thinking: OFF** — Standard-Modus

Erkenntnis aus Tests: Reasoning bringt bei Spam-Klassifikation oft keinen Vorteil und ist deutlich langsamer.

### Ergebnis-Dateien

| Datei | Inhalt |
|-------|--------|
| `benchmark/model_scores.csv` | Leaderboard aller getesteten Modelle (akkumuliert über mehrere Läufe) |
| `benchmark/detailed_results.csv` | Jede einzelne Entscheidung mit Mail-ID, Erwartung, Vorhersage |
| `benchmark/recommendation.txt` | Automatisch generierte Zusammenfassung mit Gewinner und Insights |

---

## 2. Real‑Data Benchmark (`make benchmark-real`)

Testet Modelle auf deinen echten Mails aus `data/training/`. Der Bayesian‑Filter scoret jede Mail vorab und teilt sie in drei Gruppen — genau wie in Produktion. Das Modell erhält den Bayesian‑Score als Hint (z.B. `BAYESIAN‑SCORE: 0.43 (UNSICHER)`), wie im Filtervorgang.

Das macht diesen Benchmark zum aussagekräftigsten Test für deinen Einsatzfall.

### Starten

```bash
# Interaktiv — Modell aus Liste wählen (inkl. "Alle Modelle" Option)
make benchmark-real

# Direkt mit Modellname
make benchmark-real MODEL=gemma3:12b

# Für Prompt-Optimierung: Lauf mit Label kennzeichnen
make benchmark-real MODEL=gemma3:12b LABEL=v1-original
make benchmark-real MODEL=gemma3:12b LABEL=v2-neuer-prompt
```

### Batch-Modus: Alle Modelle

Im interaktiven Wizard ist `[ Alle Modelle — Batch-Benchmark ]` die erste Option. Damit werden alle installierten Chat-Modelle nacheinander auf denselben Mails getestet. Embedding-Modelle (z.B. `nomic-embed-text`) werden automatisch herausgefiltert.

Richtwert: ~2–4 Stunden für 10 Modelle × 75 Mails.

### Die drei Testgruppen

Der Bayesian‑Filter läuft vorab über alle `.eml`‑Dateien in `data/training/spam/` und `data/training/ham/` und verteilt sie nach Score:

```
Bayesian‑Score 0.00 ──────────────────────────────── 1.00
               │          │                │
              HAM        UNSICHER         SPAM
            (< 0.30)   (0.30–0.50)      (> 0.50)
                            │
                      G1: LLM‑Aufgabe
```

| Gruppe | Inhalt | Mails | Score‑Gewicht |
|--------|--------|-------|---------------|
| **G1 – Unsicher** | Bayesian‑Score 0.30–0.50 — weder klar HAM noch klar SPAM. Das sind die Fälle, die der Filter in Produktion ans LLM gibt. Balanciert: je 15 SPAM + 15 HAM. | 30 | **60%** |
| **G2 – Klares HAM** | Score < 0.30 — Mails, die der Bayesian klar als HAM erkennt. Testet, ob das LLM legitime Mails fälschlich als SPAM markiert (False Positives). | 30 | **30%** |
| **G3 – Klarer Spam** | Score > 0.80 — Mails, die der Bayesian klar als SPAM erkennt. Konfidenz‑Check: Ein gutes Modell muss hier zuverlässig SPAM sagen. | 15 | Nur Report |

**Warum G1 balanciert (50/50)?** Ohne Balancierung enthält G1 oft deutlich mehr HAM als SPAM (der Bayesian filtert HAM schlechter als SPAM). Ein Modell, das immer "HAM" antwortet, würde so ~67% G1‑Accuracy erzielen, ohne wirklich zu klassifizieren. Die 50/50‑Balancierung verhindert diesen Trick.

### Score-Berechnung

```
Score (0–100) = G1-Accuracy% × 0.6
              + HAM-Preservation% × 0.3
              + Speed-Score × 0.1

Speed-Score = min(10.0, 50.0 / Sekunden-pro-Mail)
  → 5s/Mail  = 10 Punkte (Maximum)
  → 10s/Mail =  5 Punkte
  → 20s/Mail =  2.5 Punkte
```

### Die entscheidenden Metriken

**G1-Accuracy (Gewicht 60%)** — Wie gut klassifiziert das Modell die schwierigen Grenzfälle, bei denen der Bayesian-Filter unsicher ist? Das ist das Kernkriterium, weil das LLM in Produktion nur diese Mails zu sehen bekommt.

**HAM-Preservation / False Positive Rate (Gewicht 30%)** — Wie viele legitime Mails (G2) werden fälschlich als Spam markiert? Ein False Positive ist im Alltag schlimmer als ein verpasster Spam: wichtige Mails landen im Spam-Ordner.

```
False Positive Rate (FP) = Anzahl legitimer Mails → fälschlich als SPAM
HAM-Preservation%        = (G2-Mails korrekt als HAM) / G2-Gesamt × 100
```

**G3-Accuracy (im Report, kein Score-Gewicht)** — Erkennt das Modell offensichtlichen Spam? Wenn G3-Acc unter 70% liegt, hat das Modell ein grundlegendes Problem mit dem Prompt-Format oder der Instruktionsbefolgung.

**False Negatives (FN)** — Wie viele Spam-Mails werden als HAM durchgelassen? Für G1-Spam-Mails: wie oft versagt das Modell wo der Bayesian schon unsicher war.

**Avg/s (Sekunden pro Mail)** — Direkt relevant für den Produktionseinsatz. Bei 100 Mails/Tag und 10s/Mail sind das ~17 Minuten pro Filterlauf.

### Ergebnis-Dateien

Jeder Lauf erzeugt zwei neue Dateien mit Timestamp — frühere Läufe werden nie überschrieben:

| Datei | Inhalt |
|-------|--------|
| `benchmark/real_scores_<ts>.csv` | Score-Übersicht aller getesteten Modelle mit allen Metriken |
| `benchmark/real_details_<ts>.csv` | Jede einzelne Entscheidung: Gruppe, Label, Vorhersage, Bayesian-Score, Dauer, Betreff |

Spalten in `real_details_<ts>.csv`:

| Spalte | Bedeutung |
|--------|-----------|
| `run_label` | Bezeichnung des Laufs (leer wenn kein `--label` angegeben) |
| `model` | Modellname |
| `group` | `g1`, `g2` oder `g3` |
| `label` | Erwartetes Ergebnis: `SPAM` oder `HAM` |
| `predicted` | Vorhersage des Modells: `SPAM` oder `HAM` |
| `category` | Detailkategorie: `SPAM`, `PHISHING`, `COMMERCIAL`, `HAM` |
| `confidence` | Konfidenz-Angabe des Modells: `HOCH`, `MITTEL`, `NIEDRIG` |
| `correct` | `True` / `False` |
| `bayesian_score` | Bayesian-Score der Mail (0.0–1.0) |
| `duration_sec` | Antwortzeit in Sekunden |
| `subject` | Betreff (erste 80 Zeichen) |

---

## Benchmark zur Prompt-Optimierung

Der Real-Benchmark ist das ideale Werkzeug, um `config/system_prompt.txt` zu verbessern:

**Workflow:**

```bash
# 1. Baseline messen
make benchmark-real MODEL=gemma3:12b LABEL=v1-original

# 2. system_prompt.txt anpassen
nano config/system_prompt.txt

# 3. Neuen Lauf mit gleichem Modell und neuem Label
make benchmark-real MODEL=gemma3:12b LABEL=v2-strenger

# 4. Beide CSVs öffnen und nach run_label filtern
# oder beide in Excel/Numbers laden und G1-Acc + FP vergleichen
```

**Was zeigt Verbesserung?**
- G1-Accuracy steigt (mehr korrekte Grenzfall-Entscheidungen)
- False Positives sinken (weniger legitime Mails als Spam)
- False Negatives sinken (weniger Spam-Mails durchgelassen)

**Reproducibility:** Der Benchmark verwendet `RANDOM_SEED = 42` — alle Läufe sehen dieselben 75 Mails in derselben Reihenfolge. Der Vergleich zwischen Prompt-Varianten ist damit vollständig fair, auch wenn die Läufe Tage auseinanderliegen.

---

## Benchmark-Ergebnisse (Stand: 2026-05-27)

### Real-Data Benchmark — 10 Modelle, 75 echte Mails

Getestet auf 75 echten deutschen Mails aus `data/training/` (30 G1 + 30 G2 + 15 G3).

| Rank | Modell | Score | G1-Acc | HAM-Pres | G3-Acc | FP | FN | Avg/s |
|------|--------|------:|-------:|---------:|-------:|---:|---:|------:|
| 🏆 1 | **gemma4:E4B** | **80.0** | 73.3% | 86.7% | 53.3% | 4 | 4 | 1.5s |
| 2 | ministral-3:14b | 78.0 | 70.0% | 86.7% | **93.3%** | 4 | 3 | 4.0s |
| 3 | gemma4:e2b | 76.0 | 70.0% | 80.0% | 86.7% | 6 | 6 | **1.0s** |
| 4 | qwen2.5vl:7b | 74.0 | 60.0% | **93.3%** | 73.3% | **2** | 7 | 2.2s |
| 5 | gemma3:12b | 71.3 | 70.0% | 80.0% | 93.3% | 6 | **2** | 9.4s |
| 6 | deepseek-r1:8b | 66.0 | 56.7% | 73.3% | 100% | 8 | 4 | 2.5s |
| 7 | ministral-3:8b | 59.0 | 56.7% | 50.0% | 100% | 15 | 1 | 2.7s |
| 8 | gemma3:4b | 40.0 | 50.0% | 0.0% | 100% | 30 | 0 | 3.4s |

*Zwei Modelle (`gpt-oss:120b-cloud`, `Hermes-4-14B`) lieferten ungültige Ergebnisse durch erschöpftes Token-Budget bzw. zu langes Reasoning vor der Klassifikation — nicht im Ranking.*

**Erkenntnisse aus diesem Lauf:**

- **gemma4:E4B** gewinnt durch Speed (1.5s) + gute Balance. Schwachstelle: G3-Acc 53.3% — etwas mehr als die Hälfte der klaren Spam-Fälle wird verpasst. Im Produktionseinsatz weniger kritisch, weil der Bayesian diese klar erkennbaren Fälle schon vorher filtert.
- **ministral-3:14b** ist das solideste Modell: 93.3% G3-Acc, nur 3 FN, 4 FP. Kostet 4.0s/Mail — bei 100 Mails/Tag vertretbar.
- **gemma3:12b** hat die wenigsten False Negatives (2) aber 9.4s/Mail macht es für produktiven Dauerbetrieb langsam.
- **qwen2.5vl:7b** überrascht mit den wenigsten False Positives (2) — wer primär HAM-Schutz priorisiert, sollte es in Betracht ziehen.
- **ministral-3:8b und gemma3:4b** disqualifizieren sich: 15 bzw. 30 legitime Mails als Spam markiert — im täglichen Einsatz inakzeptabel.
- **deepseek-r1:8b** produziert mit 8 FP die meisten False Positives der validen Modelle.

**Modellempfehlung:**

| Priorität | Empfehlung | Begründung |
|-----------|-----------|------------|
| Bester Gesamtscore | **gemma4:E4B** | Score 80, schnell, gute Balance |
| Höchste Präzision | **ministral-3:14b** | Score 78, 93.3% G3, nur 3 FN |
| Wenigste FP | **qwen2.5vl:7b** | Nur 2 FP, gut für empfindliche Postfächer |
| Wenigste FN | **gemma3:12b** | Nur 2 FN, aber langsam (9.4s) |
| Nicht empfohlen | gemma3:4b, ministral-3:8b | Zu viele False Positives |

---

## Modelle mit Prompt-Problemen erkennen

Der Benchmark eignet sich auch dazu, Modelle mit Prompt-Compliance-Problemen zu identifizieren:

**Symptom 1: G3-Acc = 0%, FN = 15 (alle G3-Mails als HAM)**

Das Modell antwortet gar nicht im erwarteten Format. Mögliche Ursachen:
- **Erschöpftes Token-Budget** (Cloud-Modelle): Ollama erhält leere Response → `LLM-Antwort zu kurz oder leer`
- **Falsches API-Format**: Das Modell ist nicht für `/api/chat` ausgelegt

**Symptom 2: G3-Acc = 0%, `Unbekannte LLM-Kategorie` Warnungen**

Das Modell schreibt ausführliches Reasoning vor der Klassifikation, aber `num_predict` schneidet die Antwort ab bevor das eigentliche Verdict kommt. Das Modell ignoriert die Instruktion "ERSTE ZEILE muss sein: SPAM/HAM".

In beiden Fällen ist das Modell für den Produktionseinsatz ungeeignet — der Filter würde jeden Spam durchlassen.

---

## Synthetischer Benchmark — Ältere Ergebnisse (Stand: 2026-03-10)

Zum Vergleich: Ergebnisse des synthetischen Benchmarks mit 50 englischen Test-Mails (andere Modelle, andere Testbasis).

| Rank | Modell | Score | Accuracy | TPS | FP | FN |
|------|--------|------:|---------:|----:|---:|---:|
| 🏆 1 | ministral-3:14b | 92.8 | 92.0% | 288.6 | 3 | 1 |
| 2 | ministral-3:8b | 92.8 | 92.0% | 438.7 | 4 | 0 |
| 3 | hhao/qwen2.5-coder-tools:14b | 89.2 | 88.0% | 544.1 | 5 | 1 |
| 4 | deepseek-r1:8b (Thinking:on) | 86.0 | 88.0% | 67.8 | 6 | 0 |
| 5 | deepseek-r1:8b (Thinking:off) | 83.8 | 82.0% | 208.4 | 4 | 5 |
| 6 | gemma3:12b | 74.8 | 72.0% | 137.1 | 14 | 0 |

*Hinweis: Diese Zahlen sind nicht direkt mit dem Real-Benchmark vergleichbar — andere Test-Daten (englisch, synthetisch), andere Score-Formel, andere installierten Modelle.*

---

## CLI-Referenz

### `make benchmark` (synthetisch)

```bash
make benchmark                    # Interaktive Modellauswahl
make benchmark-quick              # 5 Mails, schneller Funktionstest

# Direkt via Python:
.venv/bin/python scripts/benchmark/spam_benchmark.py --model gemma3:12b
.venv/bin/python scripts/benchmark/spam_benchmark.py --model gemma3:12b --quick
.venv/bin/python scripts/benchmark/spam_benchmark.py --input eigene_mails.yaml
.venv/bin/python scripts/benchmark/spam_benchmark.py --output mein_ordner/
```

### `make benchmark-real` (real)

```bash
make benchmark-real                          # Interaktiv (inkl. "Alle Modelle")
make benchmark-real MODEL=gemma4:e4b         # Direkt mit Modell
make benchmark-real MODEL=gemma4:e4b LABEL=v1-original   # Mit Label für Vergleich

# Mehrere Modelle direkt:
.venv/bin/python scripts/benchmark/real_benchmark.py \
    --model gemma4:e4b \
    --model ministral-3:14b \
    --label vergleich-mai-2026
```

---

## Weiterführende Dokumentation

- 🤖 [LLM.md](LLM.md) — System-Prompt, Betriebsmodi, Bayesian-Übergabe
- 🔧 [CONFIGURATION.md](CONFIGURATION.md) — `config/settings.yaml`, LLM-Einstellungen
- 📚 [AUTO_TRAINING.md](AUTO_TRAINING.md) — Wie der Filter selbst lernt
- 📖 [SETUP.md](SETUP.md) — Ollama installieren, Modelle herunterladen
