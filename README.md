# SpamGuard

> Ein lokaler, KI-gestützter Spam-Filter für E-Mail-Konten — 100% auf deiner Maschine, kein Cloud-Abonnement, kein Serverraum.

---

## Warum ich Spam-Guard gebaut habe

Die Idee zu diesem Projekt entstand, als ich keine Lust mehr hatte, mein E‑Mail‑Programm zu öffnen: Über 90 % der ungelesenen Mails waren Spam. Der Versuch, das Problem durch Abmeldungen und konsequentes Markieren zu lösen, glich dem Kampf gegen die Hydra — der Aufwand verteilte sich nur anders. Mir fiel auf, dass ich mehr Zeit mit Sortieren als mit Lesen verbringe.

Der Spamschutz des Providers brachte kaum Entlastung. Externe Dienste und Filter versprachen viel, verschoben den Aufwand aber nur und erzeugten zusätzliche Arbeit. Bei meiner Recherche nach Open‑Source‑Lösungen für den Heimeinsatz fand ich zwar einige beeindruckende Projekte, doch fast jedes erforderte erheblichen Setup‑ und Wartungsaufwand — von der oft nötigen Infrastruktur ganz zu schweigen.

Ich suchte etwas Simples: ein Werkzeug, das auf meinem Rechner läuft und meine Mails auf Knopfdruck sortiert. Im KI‑Zeitalter hatte ich große Hoffnungen, fand aber nichts Passendes. Gleichzeitig zeigte sich, dass Spambekämpfung auch ohne KI sehr effektiv sein kann. Also entwickelte ich ein kleines Tool, das mein Postfach aufräumt, bevor ich es öffne. Daraus ist Spam‑Guard entstanden, das auf drei Ebenen arbeitet:

1. Whitelisting/Blacklisting mit etablierten Listen aus dem Internet
2. Bayesian‑Filter, der selbst lernt und den Großteil der Spam‑Mails in Bruchteilen einer Sekunde erkennt
3. Optional: LLM‑Unterstützung (lokale Ollama‑Modelle) für schwierige Grenzfälle, die der Bayesian‑Filter nicht eindeutig klassifizieren kann

Die dritte Ebene ist optional — nur sinnvoll, wenn ausreichend Rechenleistung für eine lokale Ollama‑Instanz vorhanden ist. Weil ich KI‑Benchmarks mag, gibt es außerdem ein Benchmark‑Skript, das die beste lokale KI für diesen Job ermitteln kann.

Spam‑Guard ist das Ergebnis: ein mehrstufiger Filter, der lokal läuft, Ollama‑Modelle nutzen kann und sich per `make start` starten lässt — keine Infrastruktur, kein Abo, nur ein digitaler Wachmann fürs E‑Mail‑Chaos.

---

## Features

- **Sieben Filterstufen** — Whitelist → Blacklist → TLD → SPF/DKIM → DNSBL → Bayesian → LLM
- **LLM-freier Modus** — funktioniert auch ohne Ollama (nur Bayesian, ~88–90% Genauigkeit)
- **Bayesian Pre-Filter** — 70–80% aller Mails werden in ~10 ms klassifiziert, ohne LLM
- **Newsletter-Erkennung** — optionaler 3-Klassen-Modus (HAM / SPAM / NEWSLETTER) mit flexiblem Routing
- **Auto-Training** — erkannte Spam-Mails werden automatisch als Trainingssamples gespeichert
- **Externe Blacklists** — Spamhaus DROP/EDROP, Blocklist.de, Feodo Tracker, Phishing Army und weitere
- **Multi-Account** — beliebig viele IMAP-Accounts gleichzeitig
- **Benchmark-Tool** — vergleiche LLM-Modelle auf deinen eigenen Mails (mit Batch-Modus)
- **YAML-Konfiguration** — übersichtlich, keine Python-Kenntnisse nötig
- **100% lokal** — keine Cloud, keine fremden Server, keine Telemetrie

---

## Wie es funktioniert

Jede eingehende Mail durchläuft die Pipeline von oben nach unten. Sobald eine Stufe eine eindeutige Entscheidung trifft, ist die Mail fertig — die nachfolgenden Stufen werden nicht mehr ausgeführt.

```
┌─────────────────────────────────────────────────┐
│  1. WHITELIST     → sofort HAM (vertrauenswürdig)│
│  2. BLACKLIST     → sofort SPAM (bekannte Sender)│
│  3. TLD-CHECK     → verdächtige Endungen (.xyz…) │
│  4. SPF/DKIM      → Auth-Fehler als Hinweis/SPAM │
│  5. DNSBL-LOOKUP  → IP in öffentl. Blacklist?    │
│  5b.IP-BLACKLIST  → IP in lokaler CIDR-Liste?    │
│  6. BAYESIAN      → TF-IDF + Naive Bayes         │
│     < 0.3  → HAM  │  > 0.5  → SPAM              │
│     0.3–0.5 → unsicher → weiter zu Stufe 7       │
│  7. LLM (Ollama)  → semantische Analyse der      │
│                     Grenzfälle (SPAM/PHISHING/   │
│                     COMMERCIAL/HAM)              │
└─────────────────────────────────────────────────┘
```

Das LLM sieht im Produktivbetrieb etwa 8% aller Mails. Den Rest erledigen Bayesian-Filter und deterministische Regeln — schneller, ohne GPU, und oft zuverlässiger.

---

## Quick Start

### 1. Repository klonen

```bash
git clone https://github.com/kbeissert/SpamGuard.git
cd SpamGuard
```

### 2. Dependencies installieren

```bash
make install
```

### 3. Konfiguration anlegen

```bash
cp .env.example .env
cp config/accounts.yaml.example config/accounts.yaml
cp config/settings.yaml.example config/settings.yaml
cp config/blacklists.yaml.example config/blacklists.yaml
cp data/lists/whitelist.txt.example data/lists/whitelist.txt
cp data/lists/blacklist.txt.example data/lists/blacklist.txt
```

Dann `config/accounts.yaml` mit deinen IMAP-Zugangsdaten befüllen:

```yaml
accounts:
  - name: "Mein GMX"
    user: "ich@gmx.de"
    password: "mein-passwort"
    server: "imap.gmx.net"
    port: 993
    spam_folder: "Spamverdacht"
    enabled: true
```

### 4. Bayesian-Filter trainieren

Für einen guten Start: mindestens 100 Spam- und 100 HAM-Mails exportieren.

```bash
make export-spam    # Spam-Mails aus IMAP exportieren
make export-ham     # HAM-Mails aus IMAP exportieren
make train          # Bayesian-Modell trainieren
```

### 5. Filter starten

```bash
make start
```

**Ohne LLM** (Standard, empfohlen für den Anfang): funktioniert sofort, keine Ollama-Installation nötig.

**Mit LLM** (optional, für maximale Genauigkeit): Ollama installieren, Modell laden, `llm.enabled: true` in `config/settings.yaml`.

```bash
ollama pull gemma4:e4b      # Empfehlung: schnell + effizient
# oder
ollama pull ministral3:14b  # Empfehlung: höchste Präzision
```

### Die wichtigsten Befehle

```bash
make start                        # Filter starten
make start DRYRUN=1               # Trockentest (nichts verschieben)
make load-blacklists              # Externe IP/Domain-Blacklists laden
make spam adresse@domain.de       # Zur Blacklist hinzufügen
make unspam adresse@domain.de     # Zur Whitelist + Mails wiederherstellen
make benchmark                    # Synthetischer Modell-Vergleich
make benchmark-real               # Benchmark auf deinen eigenen Mails
make help                         # Alle Befehle
```

---

## Systemanforderungen

Python 3.8+. Für den LLM-Modus: [Ollama](https://ollama.com) und eines der getesteten Modelle.

| Hardware | Empfohlenes Modell | RAM |
|---|---|---|
| Bis 8 GB | gemma4:e4b | ~4 GB |
| 8–16 GB | gemma3:12b | ~8 GB |
| 16 GB+ | ministral3:14b | ~9 GB |

Getestete IMAP-Provider: GMX, Gmail, Outlook, All-Inkl, Web.de, IONOS, Strato, HostEurope und weitere.

---

## Dokumentation

| | |
|---|---|
| [SETUP.md](docs/SETUP.md) | Vollständiges Setup, Modellauswahl, Ollama-Installation |
| [CONFIGURATION.md](docs/CONFIGURATION.md) | Alle Einstellungen in `settings.yaml` |
| [BENCHMARK.md](docs/BENCHMARK.md) | Benchmark-Tools: synthetisch und real, Scoring-Methodik, Ergebnisse |
| [LLM.md](docs/LLM.md) | LLM-Integration, System-Prompt, Bayesian-Übergabe |
| [AUTO_TRAINING.md](docs/AUTO_TRAINING.md) | Selbstlernender Filter, Auto-Training-Strategie |
| [BLACKLIST_SOURCES.md](docs/BLACKLIST_SOURCES.md) | Externe Blacklists konfigurieren und erweitern |
| [UNSPAM.md](docs/UNSPAM.md) | False Positives wiederherstellen |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Häufige Probleme und Lösungen |

---

## Lizenz

Apache License 2.0 — siehe [LICENSE](LICENSE).

Copyright 2025–2026 Kay Beißert. Projektnamens-Policy: [TRADEMARK.md](TRADEMARK.md).
