# Auto-Training: Selbstlernender Spam-Filter

## Das Problem ohne Auto-Training

Ohne Feedback-Schleife lernt der Bayesian-Filter nichts aus seinen eigenen Entscheidungen:

```
Lauf 1: Mail A → SPAM erkannt → verschoben ✓
Lauf 2: Mail A (Variante) → Bayesian unsicher → LLM muss ran
Lauf 3: Mail A (neue Variante) → Bayesian immer noch unsicher → LLM muss ran
```

Das Modell bleibt eingefroren auf dem Stand des letzten manuellen `make train`. Jede neue Spam-Kampagne landet erst einmal bei LLM oder — schlimmer — als False Negative im Posteingang.

**Auto-Training schließt diese Lücke:** Jede mit hoher Sicherheit erkannte Spam-Mail wird automatisch als Trainingssample gespeichert. Das Modell lernt kontinuierlich, ohne dass der User eingreifen muss.

---

## Wie es funktioniert

### Der Kreislauf

```
Filter-Lauf
│
├─ Mail als SPAM klassifiziert
│   ├─ Verschieben in Spam-Ordner          ← wie bisher
│   └─ Sample in data/training/spam/ speichern  ← NEU
│       ├─ Hash prüfen → Duplikat? → überspringen
│       └─ Neu? → auto_<hash>.eml schreiben
│
└─ Ende des Laufs
    ├─ 0 neue Samples → nichts tun
    ├─ 1–49 neue Samples → Hinweis ausgeben
    └─ ≥ 50 neue Samples → Re-Training automatisch starten
```

### Position im Gesamt-Workflow

```
make start
  → Filter-Pipeline (7 Stufen)
  → Spam wird erkannt + verschoben
  → SpamTrainer.add_spam() für jede Spam-Mail
  → Am Ende: needs_retrain()?
      Ja → train_bayesian.py wird gestartet
      Nein → "X Samples gesammelt, Y bis Re-Training"
```

---

## Deduplizierung

Spammer verschicken identische oder nahezu identische Mails in großen Mengen. Ohne Deduplication würde eine einzige Spam-Kampagne (z.B. 200 Kopien desselben Phishing-Texts) das Modell auf genau diesen Muster-Typ übertrainieren.

**Funktionsweise:**

```python
hash = SHA256(betreff + body[:200])[:16]
dateiname = f"auto_{hash}.eml"
```

- Gleicher Betreff + gleicher Anfang → gleicher Hash → Datei existiert bereits → übersprungen
- Leichte Variation im Body (personalisierter Name, Datum) → andere erste 200 Zeichen → neuer Hash → wird gespeichert

Das ist absichtlich so: kleine Variationen einer Kampagne sind wertvolles Trainingsmaterial. Exakte Kopien sind es nicht.

---

## Cap-Strategie: Warum 500?

| Anzahl Samples | Effekt |
|---|---|
| < 100 | Modell instabil, hohe Varianz |
| 100–300 | Gute Basis, deutlich verbesserbar |
| 300–800 | **Optimaler Bereich** — Diversität überwiegt Quantität |
| > 1000 | Marginale Verbesserung, höhere Trainingszeit |
| > 5000 | Praktisch kein Gewinn mehr für Naive Bayes |

Der Standard-Cap von **500 auto_*.eml** ist bewusst gewählt: Er liegt im optimalen Bereich und verhindert, dass der Spam-Ordner über Monate unkontrolliert wächst.

**Wichtig:** Der Cap gilt nur für automatisch gesammelte Samples (`auto_*.eml`). Manuell hinzugefügte `.eml`-Dateien (ohne `auto_`-Präfix) bleiben immer erhalten.

### Rotation: Was passiert wenn der Cap erreicht ist?

Beim Hinzufügen eines neuen Samples wird geprüft ob die Anzahl der `auto_*.eml`-Dateien den Cap übersteigt. Ist das der Fall, wird das **älteste** Sample gelöscht (nach Datei-Änderungszeit sortiert).

```
Neu: auto_f3a8c2b1.eml hinzugefügt  (501 total)
→ auto_1a2b3c4d.eml gelöscht         (500 total, älteste entfernt)
```

Alte Spam-Muster verlieren nach 12+ Monaten an Vorhersagekraft — aktuelle Angriffsmuster sind wichtiger. Die Rotation stellt sicher, dass das Modell aktuell bleibt.

---

## Re‑Training

### Automatisch (Standard)

Am Ende jedes Filter‑Laufs prüft das System, ob genug neue Samples gesammelt wurden:

```
if trainer.samples_added() >= retrain_every (Standard: 50):
    start train_bayesian.py
else:
    show "X bis Re-Training"
```

Das Re‑Training läuft nach der Zusammenfassung des Filterlaufs — der Nutzer sieht den kompletten Trainings‑Output im Terminal. Beispielauszug:

```
============================================================
📊 Gesamtzusammenfassung

📚 52 neue Spam‑Samples gesammelt (330 gesamt) — starte Re‑Training...
============================================================
🔄 Auto‑Training: Bayesian‑Modell wird neu trainiert...
============================================================

📂 Lese Training‑Daten (3‑Klassen (HAM/SPAM/NEWSLETTER))...
   Spam: 330 Dateien
   HAM:  628 Dateien
   Newsletter: 1264 Dateien

✅ Training abgeschlossen
```

### Manuell (jederzeit)

```bash
make train
```

Das manuelle Training berücksichtigt alle Samples — automatisch gesammelte und manuell hinzugefügte. Es ergänzt das automatische Re‑Training, ersetzt es nicht.

---

## Datei-Konventionen

| Dateiname | Typ | Behandlung |
|---|---|---|
| `auto_f3a8c2b1.eml` | Automatisch gesammelt | Cap + Rotation, Dedup via Hash |
| `Phishing Bank.eml` | Manuell hinzugefügt | Nie automatisch gelöscht |
| `spam_0003.eml` | Manuell hinzugefügt | Nie automatisch gelöscht |

**Format einer auto-generierten .eml:**

```
From: phisher@fake-bank.de
Subject: Ihr Konto wurde gesperrt
Date: Wed, 27 May 2026 14:30:00 +0000

Sehr geehrter Kunde, wir haben ungewöhnliche Aktivitäten ...
```

Dieses Format ist identisch zu manuell exportierten `.eml`-Dateien und wird von `train_bayesian.py` genauso verarbeitet.

---

## Konfiguration

```yaml
# config/settings.yaml
auto_training:
  enabled: true

  # Maximale Anzahl automatisch gesammelter Spam-Samples
  # Älteste werden gelöscht wenn Limit überschritten
  # Manuelle Samples in data/training/spam/ bleiben unangetastet
  max_spam_samples: 500

  # Re-Training nach X neuen Samples (am Ende des Filter-Laufs)
  retrain_every: 50
```

### Parameter-Empfehlungen

| Szenario | `max_spam_samples` | `retrain_every` |
|---|---|---|
| Wenig Spam (< 5/Tag) | 300 | 20 |
| Normaler Betrieb | 500 | 50 |
| Viel Spam (> 20/Tag) | 800 | 100 |
| Nur sammeln, manuell trainieren | 500 | `false`* |

*`retrain_every: false` — Samples werden gesammelt, aber kein automatisches Re-Training. Stattdessen manuell `make train` ausführen.

### Auto-Training deaktivieren

```yaml
auto_training:
  enabled: false
```

Wenn deaktiviert: Spam wird weiterhin erkannt und verschoben, aber kein Sample wird gespeichert. Das Modell bleibt auf dem Stand des letzten manuellen Trainings.

---

## Warum kein False-Positive-Problem?

**Bedenken:** Was wenn SpamGuard eine legitime Mail falsch als Spam erkennt und als Trainingsample speichert?

**Antwort:** Auto-Training speichert nur Mails die **tatsächlich in den Spam-Ordner verschoben** werden. Für eine solche Verschiebung muss die Pipeline folgendes bestätigen:

- Bayesian-Score > 0.5 (oder LLM-Klassifikation als SPAM/PHISHING)
- LLM mit NIEDRIG-Konfidenz → kein Spam (durch Downgrade-Mechanismus)
- Whitelist-Treffer → nie Spam (deterministische Stufe 1)

Ein False Positive (legitimе Mail im Spam-Ordner) ist selten, und einzelne "falsche" Samples haben bei 500+ Trainings-Dateien praktisch keinen messbaren Einfluss auf die Modell-Qualität.

Zusätzlicher Schutz: `make unspam` verschiebt fälschlich markierte Mails zurück in den Posteingang. Das entfernt sie **nicht** automatisch aus dem Trainingskorpus — wer das möchte, löscht die entsprechende `auto_*.eml` manuell aus `data/training/spam/`.

---

## Verzeichnis-Übersicht

```
data/training/
├── spam/
│   ├── Phishing Bank.eml          ← manuell, nie gelöscht
│   ├── spam_0003.eml              ← manuell, nie gelöscht
│   ├── auto_f3a8c2b1.eml         ← automatisch gesammelt
│   ├── auto_2a9d4e7f.eml         ← automatisch gesammelt
│   └── ...                        ← bis max_spam_samples auto_* Dateien
├── ham/
│   └── ...                        ← nur manuell (kein Auto-Collect für HAM)
├── newsletter/
│   └── ...                        ← nur manuell (kein Auto-Collect, siehe unten)
└── metadata.json                  ← Stand des letzten Trainings
```

### Warum kein Auto-Collect für Newsletter?

Newsletter werden vom Filter erkannt und in einen eigenen Ordner verschoben — aber **nicht** automatisch als Trainingssamples gespeichert. Der Grund ist die Stabilität des Bayesian-Modells:

**Das Kernproblem: Klassen-Drift**

Ein Bayesian-Filter (Naive Bayes) trifft Entscheidungen auf Basis von Wahrscheinlichkeiten relativ zu allen Klassen. Wenn eine Klasse kontinuierlich wächst, während andere stagnieren, verschiebt sich die Entscheidungsgrenze — auch ohne dass sich die tatsächlichen Muster geändert haben.

```
Ohne Auto-Collect (stabil):          Mit Auto-Collect (Drift):
Newsletter: 500  ←→ HAM: 628         Newsletter: 1500  ←→ HAM: 628
Verhältnis: 0,8                      Verhältnis: 2,4  ← Modell übergewichtet Newsletter
→ Korrekte Trennlinie                → Mehr False Positives (HAM → Newsletter)
```

**Konkret:** Wenn `newsletter/` im Laufe von Monaten auf 2000+ Samples wächst, während `ham/` bei ~600 bleibt, lernt das Modell: "Newsletter-Signale sind sehr häufig — im Zweifelsfall Newsletter." Legitime E-Mails von z.B. einem Onlineshop (Bestellbestätigung) landen plötzlich im Newsletter-Ordner statt im Posteingang.

**Newsletter-Muster sind strukturell stabil**

Spam-Kampagnen ändern sich ständig (neue Absender, neue Formulierungen, neue Tricks). Newsletter hingegen folgen immer denselben strukturellen Mustern: `List-Unsubscribe`-Header, `Precedence: bulk`, typische Absender-Domains. Diese Merkmale ändern sich nicht — das Modell lernt sie einmalig und bleibt stabil.

**Fazit:** Newsletter profitieren von kuratierten, einmalig gesammelten Samples. ~400–500 hochwertige Samples sind optimaler als 2000 automatisch gesammelte.

---

## Troubleshooting

### "Auto-Training: Spam-Sample gespeichert" erscheint nicht im Log

Prüfen:
1. `auto_training.enabled: true` in `config/settings.yaml`?
2. Läuft der Filter im Dry-Run-Modus (`DRYRUN=1`)? Auto-Training ist im Dry-Run deaktiviert.
3. Wurden tatsächlich Mails als Spam klassifiziert? Bei 0 Spam-Treffern keine Samples.

### Re-Training startet nicht obwohl viele Samples gesammelt wurden

`retrain_every: 50` — es müssen **in einem einzigen Filter-Lauf** 50 neue (nicht-duplizierte) Samples gesammelt werden. Über mehrere Läufe verteilte Samples addieren sich nicht automatisch.

**Lösung:** `make train` manuell ausführen.

### "train_bayesian.py nicht gefunden"

Das Trainings-Skript wird über den `PROJECT_ROOT`-Pfad gesucht. Wenn SpamGuard nicht aus dem Projekt-Root-Verzeichnis gestartet wird, kann der Pfad falsch sein.

**Lösung:** Immer aus dem Projekt-Root starten:
```bash
cd /pfad/zu/spam-guard
make start
```

---

## Weitere Informationen

- 🤖 [LLM.md](LLM.md) — LLM-Integration und Betriebsmodi
- 🔧 [CONFIGURATION.md](CONFIGURATION.md) — Alle Konfigurationsoptionen
- 📖 [UNSPAM.md](UNSPAM.md) — Fehlerhafte Klassifizierungen korrigieren
- 🏗️ [ARCHITECTURE.md](ARCHITECTURE.md) — Technische Pipeline-Architektur
