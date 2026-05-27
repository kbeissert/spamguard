# Troubleshooting: Häufige Probleme und Lösungen

Lösungen für typische Fehler beim Betrieb des Spam-Filters.

---

## Verbindungsprobleme

### ❌ „Ollama nicht erreichbar“

Symptom:
```
❌ Ollama nicht erreichbar!
   Starte in anderem Terminal: ollama serve
```

Ursachen & Lösungen:

1. Ollama läuft nicht
```bash
# Starte Ollama
ollama serve
```

2. Falsche URL
```bash
# In config/settings.yaml prüfen: llm.url
# Standard: http://localhost:11434
curl http://localhost:11434/api/tags
```

3. Firewall blockiert
- Erlaube Localhost‑Verbindungen auf Port 11434
- macOS: Systemeinstellungen → Sicherheit → Firewall

---

### ❌ "IMAP-Fehler: LOGIN failed"

**Symptom**:
```
❌ IMAP-Fehler: LOGIN failed
💡 Mögliche Ursachen:
   - Falsches Passwort
   - IMAP nicht aktiviert
```

**Lösungen nach Provider**:

#### GMX / Web.de
1. **IMAP aktivieren**:
   - Einstellungen → POP3/IMAP → IMAP aktivieren
   
2. **Passwort prüfen**:
   ```yaml
   # In accounts.yaml
   password: "dein-richtiges-passwort"
   ```

#### Gmail
1. **App-Passwort verwenden** (NICHT normales Passwort!):
   - Gehe zu https://myaccount.google.com/apppasswords
   - Erstelle neues App-Passwort
   - Kopiere in `accounts.yaml` (ohne Leerzeichen)
   
2. **2FA aktivieren**:
   - App-Passwörter erfordern aktivierte 2-Faktor-Auth

3. **"Weniger sichere Apps"** (veraltet):
   - Nicht mehr nötig/möglich → Nutze App-Passwörter

#### Outlook/Hotmail
1. **Server prüfen**:
   ```yaml
   server: "outlook.office365.com"  # NICHT imap.hotmail.com
   ```

2. **2FA & App-Passwort**:
   - Bei aktivierter 2FA: App-Passwort erstellen
   - https://account.microsoft.com/security

#### All-Inkl / KAS
1. **IMAP aktivieren**:
   - KAS → E-Mail → Postfächer → IMAP aktivieren
   
2. **Richtiger Server**:
   ```yaml
   server: "w0xxxxx.kasserver.com"  # Deine Server-Nummer!
   ```

---

### ❌ "Verbindungsfehler: [SSL: CERTIFICATE_VERIFY_FAILED]"

**Symptom**:
SSL-Zertifikat wird nicht akzeptiert

**Lösung**:
```bash
# macOS: Install Certificates.command ausführen
/Applications/Python\ 3.x/Install\ Certificates.command

# Oder certifi aktualisieren
pip install --upgrade certifi
```

---

## Konfigurationsprobleme

### ❌ "accounts.yaml nicht gefunden"

**Symptom**:
```
FileNotFoundError: ❌ accounts.yaml nicht gefunden: /pfad/zu/accounts.yaml
```

**Lösung**:
```bash
# Erstelle aus Vorlage
cp accounts.yaml.example accounts.yaml

# Dann anpassen!
```

---

### ❌ "Keine aktiven Accounts gefunden (enabled: true)"

**Symptom**:
```
ValueError: Keine aktiven Accounts in accounts.yaml gefunden (enabled: true)
```

**Lösung**:
In `accounts.yaml` mindestens einen Account aktivieren:
```yaml
accounts:
  - name: "Account 1"
    # ... weitere Felder
    enabled: true  # ← WICHTIG: auf true setzen!
```

---

### ❌ "Fehler beim Parsen von accounts.yaml"

**Symptom**:
```
yaml.scanner.ScannerError: mapping values are not allowed here
```

**Ursachen**:

1. **Falsche Einrückung** (häufigster Fehler!)
   ```yaml
   # ❌ FALSCH (Tabs oder falsche Spaces)
   accounts:
   - name: "Test"
     user: "test"
   
   # ✅ RICHTIG (2 oder 4 Spaces konsistent)
   accounts:
     - name: "Test"
       user: "test"
   ```

2. **Fehlende Anführungszeichen** bei Sonderzeichen:
   ```yaml
   # ❌ FALSCH
   password: mein:pass:wort
   
   # ✅ RICHTIG
   password: "mein:pass:wort"
   ```

3. **Fehlender Doppelpunkt**:
   ```yaml
   # ❌ FALSCH
   name "Test"
   
   # ✅ RICHTIG
   name: "Test"
   ```

**YAML-Syntax testen**:
```bash
python -c "import yaml; yaml.safe_load(open('accounts.yaml'))"
# Kein Output = OK
# Fehler = Syntax-Problem
```

---

### ❌ "Account 'xyz' fehlen Felder: ['password', 'server']"

**Symptom**:
Pflichtfelder in Account nicht ausgefüllt

**Lösung**:
Prüfe, dass **alle** Felder vorhanden sind:
```yaml
- name: "Account Name"      # ✅ Pflicht
  user: "email@domain.de"   # ✅ Pflicht
  password: "passwort"      # ✅ Pflicht
  server: "imap.server.de"  # ✅ Pflicht
  port: 993                 # ✅ Pflicht
  spam_folder: "Spam"       # ✅ Pflicht
  enabled: true             # ✅ Pflicht
```

---

## E-Mail-Verarbeitungsprobleme

### ❌ "E-Mail-Suche fehlgeschlagen"

**Symptom**:
```
❌ E-Mail-Suche fehlgeschlagen
```

**Ursachen**:

1. **INBOX existiert nicht**:
   - Manche Provider nutzen andere Namen
   - Lösung: Prüfe Ordnerstruktur (Code-Anpassung nötig)

2. **SINCE-Datum ungültig** (bei `FILTER_MODE=days`):
   ```bash
   # Wechsel zu count-Modus zum Testen
   FILTER_MODE=count
   LIMIT=10
   ```

---

### ❌ "Spam-Verschiebung fehlgeschlagen"

**Symptom**:
```
⚠️  Verschiebung fehlgeschlagen: [TRYCREATE] No such mailbox
```

**Lösung**:

1. **Spam-Ordner existiert nicht**:
   - Erstelle Ordner manuell im E-Mail-Client
   - Oder nutze anderen Namen:
   
   ```yaml
   spam_folder: "Junk"  # Statt "Spam"
   ```

2. **Falsche Schreibweise**:
   - GMX: `"Spamverdacht"` (nicht `"Spam"`)
   - Gmail: `"[Gmail]/Spam"` (mit Klammern!)
   - Outlook: `"Junk"` (nicht `"Spam"`)

3. **Groß-/Kleinschreibung** beachten:
   ```yaml
   spam_folder: "Spam"  # ✅
   spam_folder: "spam"  # ❌ (bei manchen Servern)
   ```

---

### ❌ LLM klassifiziert nicht korrekt

**Symptom**:
E-Mails werden alle als HAM klassifiziert, obwohl offensichtlich Spam

**Ursachen & Lösungen**:

1. **Falsches Modell**:
   ```bash
   # In ollama.yaml anpassen - Empfohlene Modelle für deutsche E-Mails
   model: gemma3:12b       # Guter Kompromiss (~8GB RAM)
   model: ministral3:14b   # Beste Erkennungsrate (~9GB RAM)
   model: gemma4:e4b       # Schnell, weniger RAM (~4GB)
   ```
   
   💡 Siehe [Modellübersicht in SETUP.md](SETUP.md#modellauswahl) für Details

2. **Modell nicht geladen**:
   ```bash
   ollama pull gemma3:12b
   ```

3. **LLM-Ausgabe prüfen** (Debug):
   - Prüfe Log-Datei: `tail -f ~/spam_filter.log | grep -i "llm\|spam\|ham"`
   - Das System erwartet als erste Zeile: `SPAM`, `PHISHING`, `COMMERCIAL` oder `HAM`

---

## Bayesian Filter Probleme

### ❌ "Kein Bayesian-Modell gefunden"

**Fehlermeldung**:
```
⚠️  Kein Bayesian-Modell gefunden: data/models/bayesian_model.pkl
   Führe 'make train' aus, um Bayesian-Filter zu aktivieren.
   Bis dahin: LLM-Only-Modus
```

**Ursache**:  
Du hast den Bayesian Filter aktiviert (`bayesian.enabled: true` in `config/bayesian.yaml`), aber noch kein Modell trainiert.

**Lösung**:

1. **Prüfe ob Training-Daten vorhanden**:
   ```bash
   ls data/training/spam/*.eml
   ls data/training/ham/*.eml
   ```

2. **Wenn keine .eml Dateien:**
   ```bash
   # Exportiere aus IMAP
   make export-spam
   make export-ham
   
   # Oder: Lege manuell .eml Dateien ab
   ```

3. **Training starten**:
   ```bash
   make train
   ```

4. **Prüfe ob Modell erstellt wurde**:
   ```bash
   ls -lh data/models/bayesian_model.pkl
   ls -lh data/models/vectorizer.pkl
   ```

---

### ❌ "Training mit 0 Spam + 0 HAM Mails"

**Fehlermeldung**:
```
📂 Lese Training-Daten...
   Spam: 0 Dateien
   HAM:  0 Dateien

❌ Keine Spam .eml Dateien gefunden in: data/training/spam
   Lege mindestens 1 Spam-Mail als .eml Datei dort ab.
```

**Ursache**:  
Die Verzeichnisse `data/training/spam/` und `data/training/ham/` sind leer.

**Lösung**:

1. **Option A: Automatischer Export**:
   ```bash
   make export-spam   # Exportiert aus IMAP Spam-Ordner
   make export-ham    # Exportiert aus Sent + INBOX/Whitelist
   ```

2. **Option B: Manueller Export**:
   - Exportiere E-Mails aus deinem E-Mail-Client als `.eml` Dateien
   - Kopiere Spam nach `data/training/spam/`
   - Kopiere legitime Mails nach `data/training/ham/`

**⚠️ WICHTIG - Newsletter vs. Spam:**
- Newsletter gehören zu **HAM**, nicht SPAM!
- Nur echter Betrug/Scam in `spam/` Ordner

---

### ❌ "Training fehlgeschlagen: No module named 'sklearn'"

**Fehlermeldung**:
```
ModuleNotFoundError: No module named 'sklearn'
```

**Ursache**:  
`scikit-learn` ist nicht installiert.

**Lösung**:

```bash
# Via Makefile (empfohlen)
make install

# Oder manuell
pip install scikit-learn
```

**Prüfe Installation**:
```bash
python -c "import sklearn; print(sklearn.__version__)"
# Sollte Version ausgeben (z.B. 1.8.0)
```

---

### ❌ "Bayesian Score immer 0.5 (neutral)"

**Symptom**:  
Filter gibt für alle Mails Score 0.5 aus und nutzt immer LLM-Fallback.

**Ursache**:  
Modell ist nicht bereit (ready = False) oder `predict_score()` hat Fehler.

**Lösung**:

1. **Prüfe ob Modell geladen wurde**:
   ```bash
   make train-stats
   ```

   Sollte zeigen:
   ```
   ✅ Modell bereit: data/models/bayesian_model.pkl
   ```

2. **Wenn "Modell nicht bereit"**:
   - Führe `make train` aus
   - Prüfe ob `.eml` Dateien vorhanden sind

3. **Wenn Modell existiert, aber nicht lädt**:
   ```bash
   # Prüfe Modell-Datei
   file data/models/bayesian_model.pkl
   # Sollte: "data" zeigen (Pickle-Datei)
   
   # Falls korrupt: Neu trainieren
   rm data/models/bayesian_model.pkl
   rm data/models/vectorizer.pkl
   make train
   ```

---

### ⚠️ "Niedrige Datenmenge — Genauigkeit < 85%"

**Warnung**:
```
⚠️  Hinweis: < 100 Mails pro Kategorie
   Genauigkeit kann < 85% sein
   Ziel: 100+ Spam + 100+ HAM für beste Ergebnisse
```

**Bedeutung**:  
Du hast weniger als 100 Mails pro Kategorie. Der Filter funktioniert, aber mit geringerer Genauigkeit.

**Lösung**:

1. **Sammle mehr Mails**:
   ```bash
   # Exportiere mehr aus IMAP
   make export-spam   # Erhöht limit in scripts/export_training_data.py
   make export-ham
   ```

2. **Oder: Akzeptiere niedrigere Genauigkeit**:
   - Mit 10+10 Mails: ~75-80% Genauigkeit
   - Mit 50+50 Mails: ~85-88% Genauigkeit
   - Mit 100+100 Mails: ~88-90% Genauigkeit

---

### ❌ "Filter markiert alles als Spam"

**Symptom**:  
Bayesian Filter klassifiziert fast alle Mails als SPAM, auch legitime.

**Ursache**:  
Newsletter wurden als SPAM trainiert → Filter lernt "zalando.de = SPAM".

**Lösung**:

1. **Prüfe Training-Daten**:
   ```bash
   ls data/training/spam/
   ls data/training/ham/
   ```

2. **Wenn Newsletter in spam/**:
   ```bash
   # Verschiebe Newsletter nach ham/
   mv data/training/spam/newsletter_*.eml data/training/ham/
   ```

3. **Neu trainieren**:
   ```bash
   make train
   ```

**Regel**:  
✅ Newsletter → HAM (auch wenn nervig)  
❌ Newsletter → SPAM (führt zu False Positives)

---

### ❌ "CV Folds = 2 statt 5"

**Ausgabe bei Training**:
```
✅ Training abgeschlossen!
   CV Folds: 2
```

**Bedeutung**:  
Du hast sehr wenig Trainingsdaten (< 25 Mails pro Kategorie).

**Ist das ein Problem?**  
Nicht unbedingt, aber Genauigkeit ist niedriger:
- CV=2: ~75-80% Genauigkeit
- CV=5: ~88-90% Genauigkeit

**Lösung**:  
Sammle mindestens 25 Spam + 25 HAM Mails für CV=5.

**Faustregel**:
- < 10 Mails: CV=2
- 10-24 Mails: CV=2
- 25-49 Mails: CV=5
- 50+ Mails: CV=5

---

## Performance-Probleme

### 🐌 "Script ist sehr langsam"

**Ursachen & Lösungen**:

1. **Großes Modell**:
   ```bash
   # Schnelleres Modell in ollama.yaml nutzen
   model: gemma4:e4b   # Statt gemma3:12b
   ```

2. **Zu viele E-Mails**:
   ```bash
   # Limit reduzieren
   LIMIT=20  # Statt 50+
   ```

3. **CPU-Last**:
   - Ollama nutzt CPU/GPU intensiv
   - Schließe andere Programme
   - Nutze GPU-beschleunigtes Ollama (CUDA/Metal)

4. **Netzwerk-Timeouts**:
   - Langsame IMAP-Server
   - VPN kann verlangsamen

**Geschwindigkeitsvergleich**:
| Modell | ~Zeit/E-Mail | Empfehlung |
|--------|--------------|------------|
| gemma4:e4b | ~1s | ⚡ Schnell, wenig RAM |
| gemma3:12b | ~2s | ✅ Guter Kompromiss |
| ministral3:14b | ~3s | 🎯 Beste Erkennungsrate |

---

## Log-Probleme

### ❌ "Permission denied: ~/spam_filter.log"

**Symptom**:
Log-Datei kann nicht erstellt werden

**Lösung**:
```bash
# Berechtigungen prüfen
ls -la ~/spam_filter.log

# Datei löschen und neu erstellen lassen
rm ~/spam_filter.log

# Oder anderen Pfad nutzen
# In .env:
LOG_PATH=/tmp/spam_filter.log
```

---

### 📄 "Log-Datei zu groß"

**Symptom**:
Log-Datei wächst auf mehrere MB/GB

**Lösung**:
```bash
# Log rotieren
mv ~/spam_filter.log ~/spam_filter.log.old
gzip ~/spam_filter.log.old

# Log truncaten
> ~/spam_filter.log  # Leert Datei

# Automatische Rotation (Linux)
logrotate /etc/logrotate.d/spam-filter
```

---

## Allgemeine Debugging-Tipps

### 0. Verbindungen testen

**Vor dem Debugging**: Nutze das Test-Script!
```bash
python test_connection.py
```

Prüft automatisch:
- ✅ Ollama-Verbindung
- ✅ LLM-Modell verfügbar
- ✅ IMAP-Login für alle Accounts
- ✅ Spam-Ordner vorhanden

### 1. Verbose-Logging aktivieren

In `src/spam_filter.py` ändern:
```python
logging.basicConfig(
    filename=log_path,
    level=logging.DEBUG,  # Statt INFO
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

### 2. Einzelnen Account testen

In `accounts.yaml` alle außer einem deaktivieren:
```yaml
accounts:
  - name: "Test"
    enabled: true   # ← Nur dieser aktiv
  - name: "Account 2"
    enabled: false  # ← Deaktiviert
```

### 3. Python-Fehler analysieren

```bash
# Mit Traceback
python src/spam_filter.py 2>&1 | tee error.log

# Syntax-Check
python -m py_compile src/spam_filter.py
```

### 4. Konfiguration ausgeben

```bash
python -c "
import ollama_client
from config import EMAIL_ACCOUNTS, FILTER_MODE, LIMIT, DAYS_BACK
print('Modell:', ollama_client.MODEL)
print('Accounts:', len(EMAIL_ACCOUNTS))
print('Filter:', FILTER_MODE, LIMIT, DAYS_BACK)
"
```

---

## Bekannte Einschränkungen

### Gmail Quota
- Gmail limitiert IMAP-Zugriffe
- Bei Überschreitung: Warte 24h oder nutze `LIMIT=10`

### Multipart/Alternative E-Mails
- HTML-only E-Mails haben keinen Text-Body
- Script nutzt Fallback auf HTML (begrenzt)

### Nicht-UTF-8 Kodierung
- Exotische Zeichenkodierungen können Probleme machen
- Script nutzt `errors='ignore'` als Fallback

---

## Häufige Fehlermeldungen

| Fehler | Bedeutung | Lösung |
|--------|-----------|--------|
| `AUTHENTICATIONFAILED` | Login fehlgeschlagen | Passwort/Username prüfen |
| `[TRYCREATE]` | Ordner existiert nicht | Spam-Ordner erstellen |
| `ConnectionRefusedError` | Ollama läuft nicht | `ollama serve` starten |
| `ModuleNotFoundError` | Dependency fehlt | `pip install -e .` oder `make install` |
| `yaml.scanner.ScannerError` | YAML-Syntax falsch | Einrückung prüfen |

---

## Hilfe erhalten

### 1. Log-Datei prüfen
```bash
tail -50 ~/spam_filter.log
```

### 2. Issue erstellen
- Füge relevante Log-Auszüge bei
- Gib Provider an (GMX, Gmail, etc.)
- **NIEMALS** Passwörter posten!

### 3. Debug-Info sammeln
```bash
# System
python --version
pip list | grep -E "dotenv|requests|tqdm|yaml"

# Ollama
ollama list
curl -s http://localhost:11434/api/tags | python -m json.tool

# Config (OHNE Passwörter!)
cat .env | grep -v PASSWORD
```

---

## Weiterführende Dokumentation

- **Setup & Installation**: [SETUP.md](SETUP.md)
- **Konfiguration**: [CONFIGURATION.md](CONFIGURATION.md)

---

## Benchmark-Probleme

### ❌ "No module named 'pandas'" (oder andere Module)

**Symptom**:
Der Benchmark startet nicht und meldet fehlende Python-Module.

**Lösung**:
Du nutzt wahrscheinlich nicht das virtuelle Environment.
1.  Führe `make install` aus, um alle Abhängigkeiten zu installieren.
2.  Starte den Benchmark immer mit `make benchmark` (das nutzt automatisch das richtige Environment).

### ❌ "No models found in Ollama"

**Symptom**:
Die Liste der Modelle im Benchmark ist leer oder es erscheint eine Warnung.

**Lösung**:
1.  Stelle sicher, dass Ollama läuft (`ollama serve`).
2.  Prüfe, ob du Modelle heruntergeladen hast:
    ```bash
    ollama list
    ```
3.  Falls leer, lade ein Modell:
    ```bash
    ollama pull qwen2.5:14b-instruct
    ```
