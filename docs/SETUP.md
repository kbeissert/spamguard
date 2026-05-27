# Setup-Anleitung: Spam Guard

Schritt‑für‑Schritt‑Anleitung zur Ersteinrichtung des lokalen Spam‑Filters.

---

## Voraussetzungen

### System
- **Python**: Version 3.8 oder höher
- **Ollama**: Installiert und lauffähig
- **Betriebssystem**: macOS, Linux oder Windows (WSL)

### IMAP-Zugang
- E-Mail-Account mit aktiviertem IMAP
- IMAP-Server-Adresse und Port
- Login-Daten (bei Gmail: App-Passwort erforderlich!)

---

## Installation

### 1. Repository klonen / herunterladen

```bash
git clone <repository-url> spam-guard
cd SpamGuard
```

Oder ZIP herunterladen und entpacken.

---

### 2. Python‑Dependencies installieren

Wir verwenden ein **virtuelles Environment** (`.venv`), um Konflikte mit anderen Projekten zu vermeiden. Das `Makefile` richtet das automatisch ein.

```bash
make install
```

Der Befehl:
1. Erstellt `.venv` im Projektverzeichnis
2. Installiert die benötigten Pakete via `pip install -e .` (nutzt `pyproject.toml`)

Hinweis: Du musst das Environment nicht manuell aktivieren — alle `make`‑Befehle (z. B. `make start`, `make benchmark`) nutzen automatisch das richtige Python aus `.venv`.

---

### 3. Ollama einrichten

#### Ollama installieren
```bash
# macOS (Homebrew)
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: Download von https://ollama.ai/download
```

#### Ollama starten
```bash
ollama serve
```

Läuft standardmäßig auf `http://localhost:11434`

**Wichtig**: Ollama muss während der Spam-Filterung laufen!
- Starte `ollama serve` in einem separaten Terminal
- Oder starte als Hintergrund-Dienst (siehe unten)

**Ollama als Dienst (optional)**:
```bash
# macOS (läuft automatisch nach Installation)
brew services start ollama

# Linux (systemd)
sudo systemctl enable ollama
sudo systemctl start ollama
```

#### LLM‑Modell herunterladen
```bash
# Empfohlen (mittlere Systeme, ~16GB RAM)
ollama pull gemma3:12b

# Für starke Systeme (beste Erkennungsrate)
ollama pull ministral3:14b

# Für schwache Systeme / schnelle Tests
ollama pull gemma4:e4b
```


## Modellauswahl

Die Wahl des richtigen Modells hängt von deiner Hardware und deinen Anforderungen ab:

### Empfohlene Modelle (primäre Auswahl)

| Modell | Größe | Geschwindigkeit | Genauigkeit | Empfehlung |
|--------|-------|-----------------|-------------|------------|
| **gemma4:e4b** | ~4GB | ⚡⚡⚡ Schnell | ⭐⭐⭐⭐ Sehr gut | **✅ Schwache Systeme (≤8GB RAM)** |
| **gemma3:12b** | ~8GB | ⚡⚡ Mittel | ⭐⭐⭐⭐⭐ Exzellent | **✅ Mittlere Systeme (8–16GB RAM)** |
| **ministral3:14b** | ~9GB | ⚡⚡ Mittel | ⭐⭐⭐⭐⭐ Exzellent | **🏆 Starke Systeme (16GB+)** |

Alle drei Modelle erhalten denselben Chain-of-Thought System-Prompt und klassifizieren in 4 Kategorien: **SPAM / PHISHING / COMMERCIAL / HAM**.

### Alternative Modelle

| Modell | Größe | Geschwindigkeit | Genauigkeit | Besonderheiten |
|--------|-------|-----------------|-------------|----------------|
| qwen2.5:7b | ~5GB | ⚡⚡ Schnell | ⭐⭐⭐ Gut | Mehrsprachig |
| qwen2.5:14b-instruct | ~9GB | ⚡ Mittel | ⭐⭐⭐⭐ Sehr gut | Solide Alternative |

**Modell installieren**:
```bash
# Primäre Empfehlung
ollama pull gemma3:12b
```

--- 4. Konfigurationsdateien erstellen

#### .env erstellen
```bash
cp .env.example .env
```

**Bearbeite `.env`** (Pfade und Listen-Einstellungen):
```bash
# Pfade (Standard-Werte sind meist OK)
ACCOUNTS_FILE=config/accounts.yaml
LOG_PATH=~/spam_filter.log
```

#### settings.yaml erstellen
```bash
cp config/settings.yaml.example config/settings.yaml
```

**Bearbeite `config/settings.yaml`** (filter-Sektion für erste Tests):
```yaml
filter:
  mode: "count"
  limit: 5   # Für erste Tests niedrig wählen
```

#### settings.yaml erstellen
```bash
cp config/settings.yaml.example config/settings.yaml
```

**Bearbeite `config/settings.yaml`**:
```yaml
llm:
  enabled: false  # true = LLM-Modus (erfordert Ollama)
  url: "http://localhost:11434"
  model: "gemma3:12b"   # Das mit ollama pull geladene Modell

filter:
  mode: "count"
  limit: 20   # Für erste Tests niedrig wählen

bayesian:
  enabled: true
  thresholds:
    hard_ham: 0.3
    hard_spam: 0.5
```

#### accounts.yaml erstellen
```bash
cp config/accounts.yaml.example config/accounts.yaml
```

**Bearbeite `config/accounts.yaml`**:
```yaml
accounts:
  - name: "Mein Hauptaccount"
    user: "deine@email.de"
    password: "dein-passwort"
    server: "imap.gmx.net"      # Server deines Providers
    port: 993                    # Meist 993 für SSL
    spam_folder: "Spamverdacht" # Provider-spezifisch!
    enabled: true                # WICHTIG: auf true setzen!
```

**Provider-spezifische Server**:

| Provider | IMAP-Server | Port | Spam-Ordner | Besonderheiten |
|----------|-------------|------|-------------|----------------|
| **GMX** | `imap.gmx.net` | 993 | `Spamverdacht` | IMAP muss in Einstellungen aktiviert sein |
| **Gmail** | `imap.gmail.com` | 993 | `[Gmail]/Spam` | **App-Passwort erforderlich!** (siehe unten) |
| **Outlook/Hotmail** | `outlook.office365.com` | 993 | `Junk` | Nicht `imap.hotmail.com` verwenden |
| **Web.de** | `imap.web.de` | 993 | `Spamverdacht` | Wie GMX |
| **All-Inkl/KAS** | `w0xxxxx.kasserver.com` | 993 | `Spam` | Deine Server-Nummer einsetzen |
| **HostEurope** | `imap.hosteurope.de` | 993 | `Spam` | - |
| **1&1/IONOS** | `imap.ionos.de` | 993 | `Spam` | - |
| **Strato** | `imap.strato.de` | 993 | `Spam` | - |

---

### 5. Gmail App-Passwort erstellen (nur für Gmail)

Gmail erlaubt keine normalen Passwörter für IMAP!

1. Gehe zu [Google Account Security](https://myaccount.google.com/security)
2. Aktiviere **2-Faktor-Authentifizierung** (falls noch nicht aktiv)
3. Gehe zu [App-Passwörter](https://myaccount.google.com/apppasswords)
4. Wähle **Mail** und **Anderes Gerät**
5. Kopiere das generierte Passwort (16 Zeichen ohne Leerzeichen)
6. Trage es in `accounts.yaml` ein:

```yaml
- name: "Gmail"
  user: "max@gmail.com"
  password: "abcdefghijklmnop"  # ← Das App-Passwort
  server: "imap.gmail.com"
  port: 993
  spam_folder: "[Gmail]/Spam"
  enabled: true
```

Speichere das in `config/accounts.yaml`.

---

## Erster Testlauf

### 1. Verbindungstest durchführen

**Wichtig**: Teste zuerst alle Verbindungen, bevor du E-Mails verarbeitest!

```bash
python test_connection.py
```

**Was wird getestet?**
1. **Ollama-Verbindung**: Ist Ollama erreichbar auf `http://localhost:11434`?
2. **LLM-Modell**: Ist das in `config/settings.yaml` (`llm.model`) konfigurierte Modell installiert?
3. **E-Mail-Accounts**: Für jeden Account in `accounts.yaml`:
   - SSL-Verbindung zum IMAP-Server
   - Login mit Benutzername/Passwort
   - INBOX-Zugriff (zeigt Anzahl der Nachrichten)
   - Spam-Ordner existiert und ist zugreifbar

**Erwartete Ausgabe bei Erfolg**:
```
🔍 IMAP Spam-Filter: Verbindungstest
============================================================

============================================================
  Test 1: Ollama-Verbindung
============================================================
✅ Ollama erreichbar: OK
   http://localhost:11434

============================================================
  Test 2: LLM-Modell 'qwen2.5:14b-instruct'
============================================================
✅ Modell 'qwen2.5:14b-instruct' verfügbar: OK

📋 Installierte Modelle (9):
   - qwen2.5:1.5b
   - qwen2.5:7b
   - qwen2.5:14b-instruct
   ...

============================================================
  Test 3: E-Mail-Accounts (1 konfiguriert)
============================================================

📬 Account 1/1: Mein Hauptaccount
   User: deine@email.de
   Server: imap.gmx.net:993
✅ SSL-Verbindung: OK
✅ Login: OK
✅ INBOX: OK
   42 Nachrichten
✅ Spam-Ordner 'Spamverdacht': OK

============================================================
  Zusammenfassung
============================================================
✅ Ollama-Verbindung: OK
✅ LLM-Modell verfügbar: OK
✅ E-Mail-Accounts: OK

============================================================
✅ Alle Tests erfolgreich!
   Du kannst jetzt das Spam-Filter-Script ausführen:
   python src/spam_filter.py
============================================================
```

**Bei Fehlern**:
- Das Script zeigt **konkrete Lösungsvorschläge** für jeden fehlgeschlagenen Test
- Häufige Probleme:
  - **Ollama nicht gestartet**: `ollama serve` ausführen
  - **Modell fehlt**: `ollama pull qwen2.5:14b-instruct`
  - **Gmail Login-Fehler**: App-Passwort statt normalem Passwort verwenden
  - **Spam-Ordner nicht gefunden**: Ordner im E-Mail-Client erstellen oder Namen in `accounts.yaml` anpassen
- Behebe die Probleme und führe `python test_connection.py` erneut aus

---

### 2. Ersten Spam-Filter-Durchlauf starten

**Wichtig**: Starte mit **niedrigem Limit** für erste Tests!

Bearbeite `config/settings.yaml` (filter-Sektion):
```yaml
filter:
  mode: "count"
  limit: 5  # Nur 5 E-Mails zum Testen
```

Dann starte das Script:
```bash
python src/spam_filter.py
```

**Erwartete Ausgabe**:
```
==============================================================
🤖 LLM-basierter IMAP Spam-Filter (Multi-Account)
==============================================================
   Modell: qwen2.5:14b-instruct
   Accounts: 1
   Filter: Letzte 5 E-Mails pro Account
   Log: /Users/you/spam_filter.log
==============================================================

🔍 Prüfe Ollama-Verfügbarkeit...
✅ Ollama läuft

────────────────────────────────────────────────────────────
📬 Account 1/1: deine@email.de
   Server: imap.gmx.net
────────────────────────────────────────────────────────────
🔌 Verbinde zu imap.gmx.net:993...
🔐 Login als deine@email.de...
📬 Öffne INBOX...

🔍 Suche letzte 5 E-Mails...
📧 Analysiere 5 E-Mail(s)...

[... Verarbeitung ...]
```

---

## Produktiv-Einrichtung

### 1. Filter-Limit erhöhen

Nach erfolgreichen Tests in `config/settings.yaml`:
```yaml
filter:
  mode: "count"
  limit: 50   # Oder höher

# Alternativ: Zeitbasiert
# mode: "days"
# days_back: 7
```

### 2. Weitere Accounts hinzufügen

In `accounts.yaml`:
```yaml
accounts:
  - name: "Hauptaccount"
    # ... bereits konfiguriert
    enabled: true

  - name: "Zweitaccount"
    user: "zweites@mail.de"
    password: "passwort"
    server: "imap.server.de"
    port: 993
    spam_folder: "Spam"
    enabled: true  # ← Aktivieren!
```

### 3. Automatisierung (optional)

#### Cronjob (macOS/Linux)
```bash
crontab -e
```

Füge hinzu (täglich um 6 Uhr):
```cron
0 6 * * * cd /pfad/zum/projekt && /usr/bin/python3 src/spam_filter.py >> ~/spam_filter_cron.log 2>&1
```

#### Launchd (macOS)
Erstelle `~/Library/LaunchAgents/com.user.spam-filter.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.spam-filter</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/pfad/zum/projekt/src/spam_filter.py</string>
    </array>
    <key>StartInterval</key>
    <integer>21600</integer> <!-- 6 Stunden = 21600 Sekunden -->
</dict>
</plist>
```

Aktivieren:
```bash
launchctl load ~/Library/LaunchAgents/com.user.spam-filter.plist
```

---

## Sicherheitshinweise

### Dateiberechtigungen

```bash
# Nur Owner kann lesen/schreiben
chmod 600 accounts.yaml
chmod 600 .env
```

### Backups

```bash
# Verschlüsseltes Backup
gpg -c accounts.yaml
# → Erstellt accounts.yaml.gpg

# Wiederherstellen
gpg accounts.yaml.gpg
```

### Git

`.gitignore` ist bereits konfiguriert:
- ✅ `accounts.yaml` wird NICHT eingecheckt
- ✅ `.env` wird NICHT eingecheckt
- ✅ `*.log` wird NICHT eingecheckt

**Niemals** diese Dateien committen (enthalten Passwörter!)

---

## 4. Bayesian Filter Training (Optional)

Der Bayesian Filter ist ein **intelligenter Pre-Filter** der 70-80% der Mails in ~10ms klassifiziert, bevor das LLM zum Einsatz kommt. Dies beschleunigt die Verarbeitung um das 2-3fache.

### Warum Bayesian Training?

**Ohne Bayesian:**
- Alle Mails gehen durch LLM (~1,6s pro Mail)
- Durchsatz: ~25 Mails/Minute

**Mit Bayesian:**
- 70-80% werden in 10ms klassifiziert
- LLM nur für schwierige Fälle
- Durchsatz: ~50-60 Mails/Minute

### Voraussetzungen

- Mindestens 100 Spam + 100 HAM E-Mails als `.eml` Dateien
- `scikit-learn` muss installiert sein (bereits in `requirements.txt` enthalten)

### Training-Workflow

#### Schritt 1: E-Mails exportieren

**Option A: Automatisch (empfohlen)**

```bash
# Exportiert Spam aus IMAP Spam-Ordner
make export-spam

# Exportiert HAM aus Sent-Ordner (60%) + INBOX/Whitelist (40%)
make export-ham
```

**Was passiert?**
- `export-spam`: Liest letzte 90 Tage aus Spam-Ordner → `data/training/spam/*.eml`
- `export-ham`: Liest aus Sent-Ordner (garantiert HAM) + INBOX mit Whitelist-Filter → `data/training/ham/*.eml`

**Option B: Manuell**

1. Exportiere E-Mails aus deinem E-Mail-Client als `.eml` Dateien
2. Kopiere Spam-Mails nach `data/training/spam/`
3. Kopiere legitime Mails nach `data/training/ham/`

**⚠️ WICHTIG - Was ist Spam und was nicht?**

✅ **SPAM** (gehört in `data/training/spam/`):
- Lotto-Gewinn-Mails, Phishing, Betrug
- Viagra/Pillen-Werbung
- Investment-Scams
- Gefälschte Bank-/PayPal-Mails

❌ **KEIN SPAM** (gehört in `data/training/ham/`):
- Newsletter (Zalando, LinkedIn, GitHub) - auch wenn nervig!
- Benachrichtigungen (Facebook, Twitter)
- Firmenmails (Arbeit, Rechnungen)
- Mails von Freunden/Familie

**Warum ist das wichtig?**  
Wenn du Newsletter als SPAM trainierst, lernt der Filter "zalando.de = SPAM" und blockiert später ALLE Mails von Zalando - auch Bestellbestätigungen!

#### Schritt 2: Training starten

```bash
make train
```

**Was passiert?**
1. Duplikate werden automatisch aus allen Trainings-Ordnern entfernt (MD5-Vergleich)
2. Alle `.eml` Dateien werden gelesen und das Modell neu trainiert

**Ausgabe:**
```
🤖 Training Bayesian Filter...

📂 Lese Training-Daten...
   Spam: 120 Dateien
   HAM:  105 Dateien

✅ Training abgeschlossen!
   Spam: 120 Mails
   HAM:  105 Mails
   CV Folds: 5
   Features: 1847

💾 Modell gespeichert: data/models/bayesian_model.pkl
```

**Was bedeutet das?**
- **CV Folds 5**: Optimale Kalibrierung (2 = wenig Daten, 5 = gut trainiert)
- **Features 1847**: Der Filter kennt 1847 Wörter/Muster
- **Dauer**: ~5-10 Sekunden für 200 Mails

**Warnung bei wenig Daten:**
```
⚠️  Hinweis: < 100 Mails pro Kategorie
   Genauigkeit kann < 85% sein
   Ziel: 100+ Spam + 100+ HAM für beste Ergebnisse
```

#### Schritt 3: Training-Statistiken prüfen

```bash
make train-stats
```

**Ausgabe:**
```
📊 Bayesian Filter Statistics
============================================================
✅ Modell bereit: data/models/bayesian_model.pkl
   Vectorizer: data/models/vectorizer.pkl
   Features: 1847
   Modell-Größe: 23.6 KB

📅 Letztes Training: 2026-05-26T18:23:47
   Spam-Mails: 120
   HAM-Mails: 105
   CV Folds: 5
```

### Konfiguration

Bayesian-Filter-Einstellungen in `config/settings.yaml`:

```yaml
bayesian:
  enabled: true           # Bayesian Filter aktivieren
  llm_fallback: false     # LLM nur bei Unsicherheit (0.3-0.5)
  
  thresholds:
    hard_ham: 0.3         # Score < 0.3 → Auto-deliver (kein LLM)
    hard_spam: 0.5        # Score > 0.5 → Auto-spam (kein LLM)
  
  training:
    min_samples_warning: 100    # Warning bei < 100 Mails
    feature_count: 5000         # TF-IDF max features
```

**Empfehlung:**  
Starte mit `llm_fallback: false` für maximale Geschwindigkeit. Aktiviere LLM-Fallback nur wenn du mehr Genauigkeit brauchst.

### Nachtrainieren

Wenn der Filter Fehler macht (False Positives/Negatives):

1. Kopiere falsch klassifizierte Mail als `.eml` in `data/training/spam/` oder `data/training/ham/`
2. Führe `make train` aus
3. Das Modell lernt die neuen Patterns dazu

**⚠️ Wichtig:** Die alten `.eml` Dateien **NICHT löschen**!  
Bei jedem `make train` wird auf ALLEN Mails neu trainiert (dauert nur ~2s für 1000 Mails).

### Optimale Trainingsmenge

| Menge | Genauigkeit | Empfehlung |
|-------|-------------|------------|
| 10 + 10 | < 85% | Nur für Tests |
| 50 + 50 | 85-88% | Minimum für Produktion |
| **100 + 100** | **88-90%** | **Empfohlen** ⭐ |
| 200 + 200 | 90-95% | Optimal |
| 500 + 500 | 95%+ | Diminishing Returns |

---

## Nächste Schritte

Nach erfolgreichem Setup:

1. **Produktiv-Betrieb einrichten**:
   - Filter-Limit erhöhen (siehe "Produktiv-Einrichtung" oben)
   - Weitere Accounts in `accounts.yaml` hinzufügen
   - Optional: Automatisierung per Cronjob/Launchd

2. **Weitere Dokumentation**:
   - 📖 [CONFIGURATION.md](CONFIGURATION.md) - Detaillierte Konfigurationsreferenz
   - 🔧 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Problemlösungen und häufige Fehler

---

## Checkliste: Setup vollständig?

Gehe diese Schritte durch, um sicherzustellen, dass alles richtig konfiguriert ist:

- [ ] **Python 3.8+** installiert (`python --version`)
- [ ] **Dependencies** installiert (`make install` oder `pip install -r requirements.txt`)
- [ ] **Ollama** läuft (`ollama serve` oder als Dienst)
- [ ] **LLM-Modell** heruntergeladen (`ollama pull gemma3:12b` oder Alternative)
- [ ] **`.env`** erstellt und angepasst (aus `.env.example`)
- [ ] **`config/settings.yaml`** erstellt und angepasst (aus `settings.yaml.example`)
- [ ] **`config/blacklists.yaml`** erstellt (aus `blacklists.yaml.example`) + `make load-blacklists`
- [ ] **`accounts.yaml`** erstellt und angepasst (aus `accounts.yaml.example`)
- [ ] Mindestens **ein Account** mit `enabled: true`
- [ ] **Verbindungstest erfolgreich** (`make test` → alle ✅)
- [ ] **Erster Testlauf erfolgreich** (`make run` mit `LIMIT=5`)
- [ ] **Log-Datei** wird erstellt und beschrieben (`~/spam_filter.log`)

✅ **Alles erledigt? Dann bist du bereit für den produktiven Einsatz!**

---

## Praktische Shortcuts (Makefile)

Das Projekt enthält ein Makefile mit praktischen Kurzbefehlen:

```bash
make help       # Alle verfügbaren Befehle anzeigen
make install    # Dependencies installieren
make test       # Verbindungstest (Ollama, LLM, IMAP)
make run        # Spam-Filter starten
make folders    # IMAP-Ordnerstruktur anzeigen
make clean      # Cache-Dateien löschen
make status     # Projekt-Status prüfen
```

**Empfohlener Workflow:**
```bash
# 1. Setup
make install

# 2. Testen
make test

# 3. Ordnerstruktur prüfen (falls Spam-Ordner unklar)
make folders

# 4. Spam-Filter starten
make run
```

---

## Tipps für den produktiven Einsatz

### Starte mit kleinen Schritten
1. **Woche 1**: `limit: 10`, täglich manuell ausführen
2. **Woche 2**: `limit: 50`, prüfe Spam-Ordner auf False Positives
3. **Ab Woche 3**: `mode: "days"` mit `days_back: 1`, per Cronjob automatisieren

### Überwache das Log
```bash
# Letzte 50 Zeilen anzeigen
tail -50 ~/spam_filter.log

# Live-Monitoring
tail -f ~/spam_filter.log
```

### False Positives vermeiden
- Prüfe regelmäßig den Spam-Ordner
- Bei häufigen Fehlern: Modell in `config/settings.yaml` (`llm.model`) wechseln
- Wichtige Absender zur Whitelist hinzufügen: `make unspam wichtig@firma.de`
