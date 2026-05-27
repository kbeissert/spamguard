# Spam Guard

🛡️ Intelligente E-Mail-Spam-Filterung mit optionalem lokalem LLM – 100% privat, keine Cloud.

> IMAP-basierter Spam-Filter mit Bayesian Pre-Filter + optionalem LLM via Ollama für maximale Genauigkeit.

**Version 0.3.0** – Konsolidierte Konfiguration + Bayesian-Verbesserungen

## Features

- ✅ **Multi-Account Support**: Mehrere E-Mail-Konten gleichzeitig verwalten
- ✅ **Lokale Spam-Erkennung**: Keine Cloud, 100% lokal via Ollama
- 🆕 **LLM-freier Modus**: Funktioniert auch OHNE Ollama (nur Bayesian, ~88-90% Genauigkeit)
- ✅ **7-Stufen-Filter**: Whitelist → Blacklist → TLD-Check → SPF/DKIM → DNSBL → Bayesian → LLM
- ✅ **Bayesian Pre-Filter**: 70-80% der Mails werden in 10ms klassifiziert (ohne LLM)
- 🆕 **Newsletter-Erkennung**: Optionaler 3-Klassen-Modus (HAM/SPAM/NEWSLETTER) mit flexiblem Routing
- ✅ **Externe Blacklists**: Automatisches Laden von Spamhaus, Blocklist.de etc.
- ✅ **IMAP-Support**: All-Inkl, Gmail, GMX, Outlook, HostEurope, Berlin.de, etc.
- ✅ **LLM-basiert**: Unterstützt `gemma3:12b`, `gemma4:e4b`, `ministral3:14b` mit 4-Kategorien-Klassifikation
- ✅ **YAML-Konfiguration**: Übersichtliche Account- und LLM-Verwaltung
- ✅ **Flexible Filter**: Nach Anzahl oder Zeitraum (letzte X Tage)
- ✅ **Benchmark-Tool**: Teste und vergleiche verschiedene LLM-Modelle (inkl. Reasoning-Support)
- ✅ **Detailliertes Logging**: Vollständige Nachverfolgbarkeit

## Quick Start

```bash
# Repository klonen oder ZIP herunterladen
git clone <your-repo-url> spam-guard
cd spam-guard
```

### 1. Dependencies installieren

**Mit Makefile:**
```bash
make install
```

**Oder manuell:**
```bash
pip install -r requirements.txt
```

### 2. Konfiguration erstellen
```bash
# .env Datei anlegen
cp .env.example .env

# Config-Dateien anlegen
cp config/accounts.yaml.example config/accounts.yaml
cp config/settings.yaml.example config/settings.yaml

# Whitelist/Blacklist anlegen
cp data/lists/whitelist.txt.example data/lists/whitelist.txt
cp data/lists/blacklist.txt.example data/lists/blacklist.txt
cp data/lists/blacklist_sources.yaml.example data/lists/blacklist_sources.yaml
```

### 3. Accounts konfigurieren
Bearbeite `accounts.yaml`:
```yaml
accounts:
  - name: "Mein GMX Account"
    user: "max@gmx.de"
    password: "mein-passwort"
    server: "imap.gmx.net"
    port: 993
    spam_folder: "Spamverdacht"
    enabled: true  # ← auf true setzen!
```

### 4. LLM-Modus aktivieren (Optional)

**Standardmäßig läuft der Filter im LLM-freien Modus** (nur Bayesian + deterministische Checks).

**Option A: LLM-freier Modus** (empfohlen für Einsteiger)
```yaml
# config/settings.yaml
llm:
  enabled: false  # Standard: kein LLM benötigt
```

✅ **Vorteile:**
- Keine Ollama-Installation nötig
- Funktioniert auf schwacher Hardware
- Schnell: ~10ms pro Mail
- ~88-90% Genauigkeit mit Bayesian Filter

⚠️ **Nachteile:**
- Keine semantische Spam-Analyse
- Weniger genau bei neuen Spam-Mustern

**Option B: LLM-Modus** (für maximale Genauigkeit)
```yaml
# config/settings.yaml
llm:
  enabled: true
```

Dann Ollama installieren:

```bash
# Ollama starten
ollama serve

# Modell installieren (Empfehlung: gemma3:12b für 16GB+ RAM)
ollama pull gemma3:12b

# Alternativ: Kompakteres Modell
ollama pull gemma4:e4b

# Alternativ: Für starke Systeme
ollama pull ministral3:14b
```

💡 **Modellauswahl**: Siehe [Modellübersicht in SETUP.md](docs/SETUP.md#modellauswahl) für eine vollständige Übersicht aller verfügbaren Modelle mit Empfehlungen basierend auf deiner Hardware.

### 5. Verbindung testen & Filter starten

**Mit Makefile (empfohlen):**
```bash
make start              # Spam-Filter starten
make spam <adresse>     # Als Spam markieren (Blacklist)
make unspam <adresse>   # Kein Spam (Whitelist + Wiederherstellen → Posteingang)
make unspam-newsletter <adresse>  # Newsletter aus Spam → Newsletter-Ordner
make show-lists         # Alle Listen anzeigen
make benchmark          # Benchmark starten
make help               # Alle verfügbaren Befehle
```

**Oder manuell:**
```bash
# Verbindungstest
python scripts/test_connection.py

# Spam-Filter starten
python src/spam_filter.py

# E-Mails wiederherstellen
python scripts/unspam.py

# Ordnerstruktur prüfen
python scripts/list_folders.py
```

## Spam-Wiederherstellung

Manchmal werden wichtige E-Mails fälschlich als Spam markiert. Das **Unspam-Tool** hilft dabei:

### Workflow

1. **Nach Spam-Filter-Lauf**: Prüfe die Spam-Absender-Übersicht
2. **Whitelist aktualisieren & Wiederherstellen**: 
   ```bash
   # Fügt zur Whitelist hinzu UND stellt E-Mails wieder her
   make unspam wichtig@firma.de
   
   # Auch für ganze Domains
   make unspam firma.de
   ```

### Listen verwalten

```bash
# Whitelist
make show-lists                        # Anzeigen
make whitelist <adresse>               # Hinzufügen (ohne Restore)

# Blacklist  
make show-lists                        # Anzeigen
make spam <adresse>                    # Hinzufügen

# Entfernen (manuell oder per Script)
python scripts/manage_lists.py whitelist remove email@test.de
python scripts/manage_lists.py blacklist remove spam@bad.com
```

Das Tool durchsucht alle Spam-Ordner, findet E-Mails von Whitelist-Absendern und verschiebt diese zurück in den Posteingang.

**Vorteile:**
- ✅ Kein manuelles Durchsuchen der Spam-Ordner nötig
- ✅ Funktioniert für alle konfigurierten Accounts
- ✅ Sicher: Nur Whitelist-Absender werden verschoben
- ✅ Dry-Run-Modus zum Testen

## Benchmark

Teste, welches LLM-Modell am besten für deine E-Mails geeignet ist. Das Benchmark-Tool misst Genauigkeit, Geschwindigkeit und Effizienz.

```bash
# Interaktiver Benchmark (Modell auswählen)
make benchmark

# Schneller Test (nur 5 E-Mails)
make benchmark-quick
```

👉 **[Ausführliche Benchmark-Dokumentation](docs/BENCHMARK.md)**

## 🤖 Bayesian Filter Training

SpamGuard nutzt einen **Bayesian Filter** als Vor-Filter, um 70-80% der Mails schnell zu klassifizieren. Das LLM wird nur für schwierige Grenzfälle verwendet. Dies reduziert die Verarbeitungszeit erheblich.

### TL;DR (Schnell-Übersicht)

**Was:** Intelligenter Pre-Filter der 70-80% der Mails in 10ms klassifiziert (ohne LLM)  
**Wie:** Trainiere mit 100+ Spam + 100+ HAM .eml Dateien via `make train`  
**Ergebnis:** 2-3x schneller, 88-90% Genauigkeit, LLM nur für schwierige Fälle

**⚠️ WICHTIG - Newsletter vs. Spam:**
- ✅ Newsletter gehören zu **HAM** (auch wenn nervig!)
- ❌ NICHT als SPAM trainieren
- **Warum:** Sonst lernt der Filter "zalando.de = SPAM" und blockiert ALLE Mails von Zalando (auch Bestellbestätigungen)
- **Lösung:** Newsletter abmelden oder Inbox-Regel erstellen

**🆕 Newsletter-Handling (3-Klassen-Modus):**

Du kannst jetzt Newsletter als **separate Kategorie** trainieren und flexibel routen:

```bash
# 1. Newsletter sammeln (Zalando, LinkedIn, GitHub, etc.)
mkdir -p data/training/newsletter
# Kopiere .eml Dateien von Newslettern hierher

# 2. Training (erkennt automatisch 3-Klassen-Modus)
make train

# 3. Konfiguriere Routing in config/bayesian.yaml:
newsletter:
  routing: "folder"      # "ham", "spam", oder "folder"
  folder: "Newsletter"   # Ziel-Ordner
```

**Routing-Optionen:**
- `"ham"`: Newsletter bleiben im Posteingang (Standard)
- `"folder"`: Newsletter → eigener Ordner (empfohlen für Clean Inbox)
- `"spam"`: Newsletter → Spam-Ordner (nur wenn wirklich unerwünscht)

👉 **[Ausführliche Newsletter-Dokumentation](docs/CONFIGURATION.md#newsletter-handling-3-klassen-modus)**

**Optimale Trainingsmenge:**

**2-Klassen-Modus (HAM/SPAM):**

| Menge | Genauigkeit | Empfehlung |
|-------|-------------|------------|
| 10 + 10 | < 85% | Nur für Tests |
| 50 + 50 | 85-88% | Minimum für Produktion |
| **100 + 100** | **88-90%** | **Empfohlen** ⭐ |
| 200 + 200 | 90-95% | Optimal |
| 500 + 500 | 95%+ | Diminishing Returns |

**3-Klassen-Modus (HAM/SPAM/NEWSLETTER):**
- Empfohlen: 100 HAM + 100 SPAM + 50-100 NEWSLETTER
- Newsletter-Erkennung funktioniert ab ~30 Samples, optimal ab 50+

### Wie es funktioniert

Die Filter-Pipeline besteht aus 7 Stufen:
```
1. Whitelist        → hard PASS (~30%)
2. Blacklist        → hard FAIL (~10%)
3. TLD-Check        → heuristic (~15%)
4. SPF/DKIM fail    → hard FAIL (~5%)
5. DNSBL Lookup     → hard FAIL (~2%)
6. Bayesian Filter  → 70% aller Mails (~30% reach here)
   - Score < 0.3    → HAM (deliver)
   - Score > 0.5    → SPAM (move)
   - Score 0.3-0.5  → UNSURE (→ Stage 7)
7. LLM (Ollama)     → final judge (~8%)
```

### Initiales Training

**Option A: Schnellstart mit Starter-Samples** (empfohlen für Tests)
```bash
make train-with-starter    # Importiert Beispiel-Mails + trainiert lokal
make start
```

**Option B: Mit eigenen E-Mails trainieren** (empfohlen für Produktion)

1. **Spam-Mails sammeln** (mindestens 100):
   ```bash
   # Exportiere aus deinem Spam-Ordner (Account 0)
   make export-spam
   
   # Oder manuell: Verschiebe .eml Dateien nach data/training/spam/
   ```

2. **Ham-Mails sammeln** (mindestens 100):
   ```bash
   # Exportiert aus Sent-Ordner (60%) + INBOX/Whitelist (40%)
   make export-ham
   
   # Oder manuell: Verschiebe .eml Dateien nach data/training/ham/
   ```

3. **Training starten:**
   ```bash
   make train
   # Bereinigt erst Duplikate, dann Training
   # Output: Training mit X Spam + Y Ham Mails... ✅ abgeschlossen!
   ```

4. **Filter nutzen:**
   ```bash
   make start
   # Filter läuft jetzt mit trainiertem Bayesian-Modell
   ```

### Nachtrainieren & Verfeinern

Wenn der Filter False Positives/Negatives produziert:

```bash
# 1. Verschiebe falsch klassifizierte Mails nach data/training/{spam,ham}/
# 2. Trainiere nach:
make train

# Das Modell lernt die neuen Patterns, alte Daten bleiben erhalten
```

**⚠️ Wichtig:** Die `.eml` Dateien **NICHT löschen** nach dem Training. Sie werden bei jedem `make train` benötigt (Retrain-Strategie auf allen Daten, dauert nur ~2s für 1000 Mails).

### Training-Statistiken

```bash
make train-stats
# Output:
# 📊 Bayesian Filter Statistics
# ✅ Modell bereit: /path/to/bayesian_model.pkl
#    Features: 5000
#    Modell-Größe: 2.4 KB
#
# 📅 Letztes Training: 2026-05-26T18:43:12
#    Spam-Mails: 480
#    HAM-Mails: 140
#    CV Folds: 5
```

### Konfiguration (`config/settings.yaml`)

```yaml
bayesian:
  enabled: true           # Bayesian Filter aktivieren
  llm_fallback: false     # LLM nur bei Unsicherheit (0.3-0.5)
  
  thresholds:
    hard_ham: 0.3         # Score < 0.3 → Auto-deliver (kein LLM)
    hard_spam: 0.5        # Score > 0.5 → Auto-spam (kein LLM)
    # Zwischen 0.3-0.5:
    #   - llm_fallback: false → default to HAM (safe choice)
    #   - llm_fallback: true  → escalate to LLM
  
  training:
    min_samples_warning: 100    # Warning bei < 100 Mails
    feature_count: 5000         # TF-IDF max features
```

### Performance-Vorteil

- **Ohne Bayesian**: ~25 Mails/Minute (LLM für jede Mail)
- **Mit Bayesian**: ~50-60 Mails/Minute (70% durch Bayesian, 8% LLM)
- **Genauigkeit**: 88-90% (Bayesian) + 95%+ (Hybrid mit LLM)

👉 **Tipp**: Starte mit `llm_fallback: false` für maximale Geschwindigkeit. Aktiviere LLM-Fallback nur wenn du mehr Genauigkeit brauchst.

## Konfiguration

### Filter-Einstellungen + LLM + Bayesian (`config/settings.yaml`)
```yaml
filter:
  mode: "days"      # oder "count"
  days_back: 7      # Tage zurück (bei mode: "days")
  limit: 50         # Anzahl E-Mails (bei mode: "count")

llm:
  enabled: false    # true = Ollama erforderlich
  model: "gemma3:12b"
  url: "http://localhost:11434"

bayesian:
  enabled: true
  thresholds:
    hard_ham: 0.3
    hard_spam: 0.5
  newsletter:
    routing: "folder"
    folder: "Newsletter"
```

**Modi:**
- `count`: Analysiert die letzten X E-Mails pro Account
- `days`: Analysiert E-Mails der letzten X Tage

### Blacklist/Whitelist System (`.env`)
```bash
USE_LISTS=true                # Aktiviert Listen-basierte Filterung
LIST_UPDATE_INTERVAL=24       # Update-Intervall für externe Listen (Stunden)
WHITELIST_FILE=data/lists/whitelist.txt
BLACKLIST_FILE=data/lists/blacklist.txt
```

### E-Mail-Accounts (`config/accounts.yaml`)
```yaml
accounts:
  - name: "Account Name"
    user: "email@domain.de"
    password: "passwort"
    server: "imap.server.de"
    port: 993
    spam_folder: "Spam"
    enabled: true
```

**Wichtig**: Nur Accounts mit `enabled: true` werden verarbeitet!

### Whitelist/Blacklist (`data/lists/`)

**Whitelist** (`whitelist.txt`) - Vertrauenswürdige Absender:
```bash
# E-Mail-Adressen (exakt)
admin@company.com

# Ganze Domains (alle E-Mails von dieser Domain)
# WICHTIG: Subdomains (z.B. marketing.trusted-domain.com) werden NICHT automatisch erkannt!
# Dies ist ein Sicherheitsfeature, um Spam von gekaperten Subdomains zu verhindern.
# Subdomains müssen separat hinzugefügt werden.
trusted-domain.com
@trusted-domain.com  # Alternative Schreibweise (wird automatisch erkannt)
```

**Blacklist** (`blacklist.txt`) - Bekannte Spam-Absender:
```bash
# Spam-Adressen
spam@badsite.com

# Spam-Domains
known-spammer.xyz
```

**Externe Blacklists** werden automatisch geladen:
- Spamhaus DROP (IP-basiert)
- Blocklist.de (IP-basiert)

💡 **Update-Intervall**: Standard 24h, konfigurierbar via `LIST_UPDATE_INTERVAL`

## Spam-Filter Logik

Das System verwendet einen **6-Stufen-Ansatz**:

```
1. WHITELIST      → E-Mail IMMER als HAM (kein Spam)
   ↓ kein Treffer
2. BLACKLIST      → E-Mail IMMER als SPAM
   ↓ kein Treffer
3. TLD-CHECK      → Verdächtige Sender-TLD (.xyz, .top, .click ...) → SPAM
   ↓ kein Treffer
4. SPF/DKIM-AUTH  → Doppelter Auth-Fail → SPAM; einzelner Fail → Hinweis für LLM
   ↓ kein hard fail
5. DNSBL-LOOKUP   → IP in externer Blacklist → SPAM
   ↓ kein Treffer
6. LLM-ANALYSE    → Intelligente Bewertung: SPAM / PHISHING / COMMERCIAL / HAM
```

**Priorität**: Whitelist > Blacklist > TLD > SPF/DKIM > DNSBL > LLM

📖 Details: [CONFIGURATION.md - Blacklist/Whitelist-System](docs/CONFIGURATION.md#blacklistwhitelist-system)

## Unterstützte E-Mail-Provider

| Provider | IMAP-Server | Port | Spam-Ordner | Besonderheiten |
|----------|-------------|------|-------------|----------------|
| GMX | imap.gmx.net | 993 | Spamverdacht | IMAP aktivieren |
| Gmail | imap.gmail.com | 993 | [Gmail]/Spam | App-Passwort erforderlich! |
| Outlook | outlook.office365.com | 993 | Junk | - |
| All-Inkl | wXXXX.kasserver.com | 993 | Spam | Server-Nr. anpassen |
| Web.de | imap.web.de | 993 | Spamverdacht | - |
| IONOS | imap.ionos.de | 993 | Spam | - |
| Strato | imap.strato.de | 993 | Spam | - |
| HostEurope | imap.hosteurope.de | 993 | Spam | - |

📖 Weitere Details: [SETUP.md](docs/SETUP.md)

## Filter-Modi

Konfiguration in `config/settings.yaml`:

### Modus "count"
Analysiert die letzten X E-Mails (neueste zuerst):
```yaml
filter:
  mode: "count"
  limit: 50
```

### Modus "days"
Analysiert alle E-Mails der letzten X Tage:
```yaml
filter:
  mode: "days"
  days_back: 7
```

## Dokumentation

- 📖 **[SETUP.md](docs/SETUP.md)** - Vollständige Setup-Anleitung mit Modellübersicht
- 🔧 **[CONFIGURATION.md](docs/CONFIGURATION.md)** - Detaillierte Konfigurationsoptionen
- 🌐 **[BLACKLIST_SOURCES.md](docs/BLACKLIST_SOURCES.md)** - Externe Blacklist-Quellen & eigene Listen hinzufügen
- ♻️ **[UNSPAM.md](docs/UNSPAM.md)** - Spam-Wiederherstellung: E-Mails aus Spam-Ordner zurückholen
- ⚠️ **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Problemlösungen & häufige Fehler

## Systemanforderungen

| Hardware | Empfohlenes Modell | RAM-Bedarf |
|----------|-------------------|------------|
| Schwach (bis 8GB) | gemma4:e4b | ~4GB |
| Mittel (8-16GB) | gemma3:12b | ~8GB |
| Stark (16GB+) | ministral3:14b | ~9GB |
