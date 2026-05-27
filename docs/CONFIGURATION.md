# Konfigurationsübersicht

## Dateien

### 1. `config/accounts.yaml` - E-Mail-Accounts
**Zweck**: Konfiguration aller E-Mail-Konten  
**Format**: YAML  
**Versionierung**: ❌ NICHT in Git (enthält Passwörter!)  

**Beispiel**:
```yaml
accounts:
  - name: "Hauptaccount"
    user: "max@gmx.de"
    password: "geheim123"
    server: "imap.gmx.net"
    port: 993
    spam_folder: "Spamverdacht"
    enabled: true  # true = aktiv, false = deaktiviert
```

**Pflichtfelder**:
- `name`: Beschreibender Name (frei wählbar)
- `user`: E-Mail-Adresse oder Username
- `password`: IMAP-Passwort (bei Gmail: App-Passwort!)
- `server`: IMAP-Server (z.B. `imap.gmx.net`)
- `port`: IMAP-Port (meist `993` für SSL)
- `spam_folder`: Name des Spam-Ordners auf dem Server
- `enabled`: `true` oder `false`

---

### 2. `config/settings.yaml` — Alle Einstellungen
Zweck: Zentrale Konfiguration für Filter, LLM und Bayesian

Format: YAML — nicht in Git (enthält persönliche Einstellungen)

Erstellen:
```bash
cp config/settings.yaml.example config/settings.yaml
```

Vollständiges Beispiel:
```yaml
# Filter: Welche E-Mails werden geprüft?
filter:
  mode: "days"      # "count" = letzte X Mails | "days" = letzte X Tage
  days_back: 7       # Tage zurück (bei mode: "days")
  limit: 50          # Anzahl E-Mails (bei mode: "count")

# LLM (Ollama) - Optional
llm:
  enabled: false     # false = kein Ollama nötig (~88-90% Genauigkeit)
  url: "http://localhost:11434"
  model: "gemma3:12b"
  timeouts:
    inference: 120
    warmup: 60
    availability: 3
  inference:
    temperature: 0.1
    num_predict: 80
  force: false            # true = LLM für jede Mail (Bayesian wird übersprungen)
  use_bayesian_score: true  # Bayesian-Score in LLM-Prompt einfügen (wenn force: true)

# Bayesian Filter
bayesian:
  enabled: true
  llm_fallback: false
  thresholds:
    hard_ham: 0.3
    hard_spam: 0.5
  model_path: "data/models/bayesian_model.pkl"
  vectorizer_path: "data/models/vectorizer.pkl"
  training:
    min_samples_warning: 100
    feature_count: 5000
    cv_folds_min: 2
    cv_folds_max: 5
  newsletter:
    routing: "folder"   # "ham", "folder" oder "spam"
    folder: "Newsletter"
```

---

#### Filter-Abschnitt (`filter:`)

| Parameter | Werte | Beschreibung |
|-----------|-------|--------------|
| `mode` | `count`/`days` | Filtermodus |
| `limit` | Zahl | Anzahl E-Mails (bei `mode: count`) |
| `days_back` | Zahl | Tage zurück (bei `mode: days`) |

---

#### LLM-Abschnitt (`llm:`)

👉 **Ausführliche Dokumentation:** [LLM.md](LLM.md) — Betriebsmodi, System-Prompt anpassen, Bayesian-Score-Übergabe, technische Details

| Parameter | Beschreibung | Standard |
|-----------|--------------|----------|
| `enabled` | `false` = kein Ollama nötig; `true` = Ollama erforderlich | `false` |
| `force` | `true` = LLM bewertet jede Mail, Bayesian nur als Hint | `false` |
| `use_bayesian_score` | Bayesian-Score in LLM-Prompt einfügen (nur wenn `force: true`) | `true` |
| `model` | Ollama-Modellname | `gemma3:12b` |
| `inference.temperature` | 0.0 = deterministisch, 1.0 = kreativ | `0.1` |
| `inference.num_predict` | Max. generierte Token (3-Zeilen-Format braucht ~50) | `80` |

**Verfügbare Modelle** (wenn `enabled: true`):

| Modell | RAM-Bedarf | Empfehlung |
|--------|------------|------------|
| `gemma4:e4b` | ~4GB | Schwache Systeme (≤8GB) |
| `gemma3:12b` | ~8GB | Mittlere Systeme (8–16GB) |
| `ministral3:14b` | ~9GB | Starke Systeme (16GB+) |

---

#### LLM-Betriebsmodi

Es gibt drei sinnvolle Kombinationen aus Bayesian und LLM. Modus D (`force: true` + `llm_fallback: true`) ist technisch möglich, verhält sich aber identisch zu Modus B, da `force` den `llm_fallback` überlagert.

---

**Modus A — Nur Bayesian** *(schnell, kein Ollama nötig)*

```yaml
llm:
  enabled: false

bayesian:
  llm_fallback: false   # oder true – hat keinen Effekt ohne llm.enabled
```

- Bayesian entscheidet alle Fälle selbst
- Unsichere Mails (0.3–0.5) → HAM (sicherer Default)
- ⚠️ Wenn `llm_fallback: true` gesetzt, aber `llm.enabled: false` → Startup-Warnung, Verhalten wie `false`
- Durchsatz: ~50–60 Mails/Minute, ~88–90% Genauigkeit

---

**Modus B — LLM für alle Mails** *(gründlich, Ollama erforderlich)*

```yaml
llm:
  enabled: true
  force: true
  use_bayesian_score: true   # Bayesian-Score als Kontext-Hint in den Prompt

bayesian:
  llm_fallback: false   # irrelevant wenn force: true
```

- Bayesian-Early-Exit wird übersprungen — LLM bewertet jede Mail nach den deterministischen Stufen (Whitelist/Blacklist/TLD/SPF/DNSBL)
- Wenn `use_bayesian_score: true`: LLM-Prompt enthält zusätzlich `BAYESIAN-SCORE: 0.42 (UNSICHER)` als Kontext
- Der `config/system_prompt.txt` bleibt davon unberührt und kann frei bearbeitet werden
- Durchsatz: ~15–25 Mails/Minute, ~94–96% Genauigkeit

---

**Modus C — Bayesian mit LLM-Fallback** *(ausgewogen, empfohlen)*

```yaml
llm:
  enabled: true
  force: false

bayesian:
  llm_fallback: true
```

- Bayesian entscheidet sichere Fälle (Score < 0.3 → HAM, Score > 0.5 → SPAM)
- Unsichere Fälle (0.3–0.5) → LLM für finale Entscheidung
- ⚠️ Beide Schalter müssen aktiv sein: `llm.enabled: true` **und** `bayesian.llm_fallback: true`
- Durchsatz: ~35–45 Mails/Minute, ~92–95% Genauigkeit

---

#### Bayesian-Abschnitt (`bayesian:`)

Der Bayesian Filter klassifiziert 70-80% der Mails in ~10ms, bevor das LLM zum Einsatz kommt. Dies beschleunigt die Verarbeitung um das 2-3fache.

**Parameter-Erklärung**:

| Parameter | Werte | Beschreibung |
|-----------|-------|--------------|
| `enabled` | `true`/`false` | Aktiviert/deaktiviert Bayesian Filter |
| `llm_fallback` | `true`/`false` | **false**: Unsichere Mails (0.3-0.5) → HAM (schnell, sicher)<br>**true**: Unsichere Mails → LLM (langsamer, genauer) |
| `thresholds.hard_ham` | 0.0-1.0 | Score unter diesem Wert = HAM (Standard: 0.3) |
| `thresholds.hard_spam` | 0.0-1.0 | Score über diesem Wert = SPAM (Standard: 0.5) |
| `model_path` | Pfad | Pfad zum trainierten Modell (.pkl) |
| `vectorizer_path` | Pfad | Pfad zum TF-IDF Vectorizer (.pkl) |
| `training.min_samples_warning` | Zahl | Warning-Schwelle für Trainingsmenge |
| `training.feature_count` | Zahl | Max TF-IDF Features (Standard: 5000) |

**Best Practices:**

#### Threshold-Tuning

**Konservativ (wenig False Positives):**
```yaml
bayesian:
  thresholds:
    hard_ham: 0.2    # Engerer HAM-Bereich
    hard_spam: 0.8   # Engerer SPAM-Bereich
  llm_fallback: true  # LLM für mehr Fälle
```

**Aggressiv (maximale Geschwindigkeit):**
```yaml
bayesian:
  thresholds:
    hard_ham: 0.4    # Breiterer HAM-Bereich
    hard_spam: 0.6   # Breiterer SPAM-Bereich
  llm_fallback: false  # Kein LLM, HAM bei Unsicherheit
```

**Standard (empfohlen):**
```yaml
bayesian:
  thresholds:
    hard_ham: 0.3
    hard_spam: 0.5
  llm_fallback: false
```

#### LLM-Fallback-Strategien

Für die Wahl des richtigen Modus siehe [LLM-Betriebsmodi](#llm-betriebsmodi) weiter oben.

**Kurzübersicht:**

| Ziel | Modus | Durchsatz |
|------|-------|-----------|
| Maximale Geschwindigkeit | A (`llm.enabled: false`) | ~50–60 Mails/min |
| Ausgewogen | C (`llm_fallback: true`) | ~35–45 Mails/min |
| Maximale Gründlichkeit | B (`force: true`) | ~15–25 Mails/min |

#### Feature-Count Optimierung

**Wenig Trainingsdaten (< 200 Mails):**
```yaml
bayesian:
  training:
    feature_count: 2000  # Reduziert Overfitting
```

**Viel Trainingsdaten (500+ Mails):**
```yaml
bayesian:
  training:
    feature_count: 10000  # Mehr Nuancen erkennen
```

#### Training-Workflow

1. **Initiales Training:**
   ```bash
   make train
   ```

2. **Nachtrainieren bei False Positives/Negatives:**
   - Kopiere falsch klassifizierte Mail als `.eml` in `data/training/{spam,ham}/`
   - Führe `make train` aus
   - Alte `.eml` Dateien NICHT löschen (Retrain auf allen Daten)

3. **Training-Statistiken prüfen:**
   ```bash
   make train-stats
   ```

**⚠️ Wichtig - Newsletter vs. Spam:**
- Newsletter gehören zu **HAM**, nicht SPAM!
- Wenn Newsletter als SPAM trainiert → Filter lernt "zalando.de = SPAM"
- Folge: ALLE Mails von Zalando werden blockiert (auch Bestellbestätigungen)

---

#### Newsletter-Handling (3-Klassen-Modus)

**Seit Version 1.5**: Der Bayesian Filter unterstützt einen optionalen 3-Klassen-Modus um Newsletter separat zu behandeln.

**Aktivierung:**

1. **Erstelle Newsletter-Trainingsdaten:**
   ```bash
   mkdir -p data/training/newsletter
   # Kopiere .eml Dateien von Newslettern (Zalando, LinkedIn, etc.) nach data/training/newsletter/
   ```

2. **Training mit 3 Kategorien:**
   ```bash
   make train
   # Erkennt automatisch den newsletter/ Ordner → 3-Klassen-Modus
   ```

3. **Konfiguriere Newsletter-Routing in `config/settings.yaml`:**
   ```yaml
   bayesian:
     newsletter:
       routing: "folder"     # "ham", "spam", oder "folder"
       folder: "Newsletter"  # Nur relevant bei routing: "folder"
   ```

**Routing-Optionen:**

| Routing | Verhalten | Anwendungsfall |
|---------|-----------|----------------|
| `"ham"` | Newsletter bleiben im Posteingang | Standard, keine Änderung am Workflow |
| `"spam"` | Newsletter → Spam-Ordner | Du möchtest Newsletter aktiv loswerden |
| `"folder"` | Newsletter → separater Ordner | Beste Option: Newsletter getrennt, aber zugänglich |

**Best Practices:**

✅ **DO:**
- Trainiere Newsletter als separate Kategorie (nicht als SPAM!)
- Nutze routing="folder" für besten Workflow
- Sammle mindestens 50+ Newsletter für gutes Training

❌ **DON'T:**
- Newsletter nicht als SPAM trainieren (führt zu False Positives!)
- Transaktions-Mails (Bestellbestätigungen) NICHT als Newsletter
- Newsletter-Ordner im E-Mail-Client nicht vergessen bei routing="folder"

---

#### Auto-Training-Abschnitt (`auto_training:`)

```yaml
auto_training:
  enabled: true
  max_spam_samples: 500
  retrain_every: 50
```

| Parameter | Typ | Beschreibung |
|---|---|---|
| `enabled` | bool | Auto-Training aktivieren/deaktivieren |
| `max_spam_samples` | Zahl | Max. auto-gesammelte Spam-Samples (älteste werden rotiert) |
| `retrain_every` | Zahl | Re-Training nach X neuen Samples im selben Lauf |

**Funktionsweise:**

Jede Mail die als SPAM in den Spam-Ordner verschoben wird, wird automatisch als `.eml`-Datei in `data/training/spam/` gespeichert. Deduplizierung verhindert, dass identische Spam-Kampagnen das Trainingsset dominieren. Am Ende des Filter-Laufs wird automatisch re-trainiert sobald `retrain_every` neue Samples gesammelt wurden.

Nur `auto_*.eml`-Dateien werden rotiert — manuell hinzugefügte `.eml`-Dateien bleiben immer erhalten.

👉 **[Ausführliche Dokumentation: AUTO_TRAINING.md](AUTO_TRAINING.md)**

---

### 3. `.env` - Pfade und Listen-Einstellungen
**Zweck**: Pfade, Listen-Konfiguration und sonstige globale Einstellungen  
**Format**: Key=Value  
**Versionierung**: ❌ NICHT in Git

> **Hinweis**: Filter-Modus (`mode`, `days_back`, `limit`) und LLM-Konfiguration sind jetzt in `config/settings.yaml` konsolidiert. Der System-Prompt ist in `config/system_prompt.txt`.

**Beispiel**:
```bash
# Pfade
ACCOUNTS_FILE=config/accounts.yaml
LOG_PATH=~/spam_filter.log
```

**Alle Optionen**:

| Variable | Werte | Beschreibung |
|----------|-------|--------------|
| `ACCOUNTS_FILE` | Pfad | Pfad zu accounts.yaml (Standard: `config/accounts.yaml`) |
| `LOG_PATH` | Pfad | Log-Datei |
| **`USE_LISTS`** | **`true`/`false`** | **Aktiviert Blacklist/Whitelist-System** |
| **`LIST_UPDATE_INTERVAL`** | **Zahl** | **Update-Intervall für externe Listen (Stunden)** |
| **`WHITELIST_FILE`** | **Pfad** | **Pfad zur lokalen Whitelist** |
| **`BLACKLIST_FILE`** | **Pfad** | **Pfad zur lokalen Blacklist** |
| **`LISTS_CACHE_DIR`** | **Pfad** | **Cache-Verzeichnis für externe Listen** |
| **`FORCE_LIST_UPDATE`** | **`true`/`false`** | **Erzwingt Listen-Update beim Start** |

---

## Blacklist/Whitelist-System

### Übersicht

Das Blacklist/Whitelist-System bietet einen **Hard Filter** in der mehrstufigen Pipeline:

**Priorität (von höchster zu niedrigster)**:
1. **Whitelist** → E-Mail wird IMMER als HAM (kein Spam) behandelt
2. **Blacklist** → E-Mail wird IMMER als SPAM behandelt
3. **TLD-Check** → Verdächtige Sender-Domain (.xyz, .top, .click…) → SPAM
4. **SPF/DKIM-Auth** → Doppelter Auth-Fail → SPAM; einzelner Fail → Hint für LLM
5. **DNSBL-Lookup** → IP in externer Blacklist → SPAM
6. **LLM-Analyse** → 4-Kategorien: SPAM / PHISHING / COMMERCIAL / HAM

### Hierarchische Domain-Prüfung (Subdomains)

Das System prüft Domains automatisch hierarchisch. Das bedeutet, wenn Sie eine Hauptdomain sperren (oder freigeben), gilt dies automatisch auch für alle Subdomains.

**Beispiel:**
Eintrag in der Liste: `example.com`

Dies betrifft:
- `user@example.com` (Exakter Treffer)
- `newsletter@shop.example.com` (Subdomain)
- `info@mail.server.example.com` (Tiefere Subdomain)

Sie müssen also **keine Wildcards** (`*`) verwenden. Geben Sie einfach die Domain an, die Sie abdecken möchten.

### Aktivierung

**.env**:
```bash
# Blacklist/Whitelist aktivieren
USE_LISTS=true

# Update-Intervall für externe Listen (Standard: 24 Stunden)
LIST_UPDATE_INTERVAL=24

# Lokale Listen (relativ zum Projekt-Root)
WHITELIST_FILE=data/lists/whitelist.txt
BLACKLIST_FILE=data/lists/blacklist.txt

# Cache-Verzeichnis für externe Listen
LISTS_CACHE_DIR=data/lists

# Erzwinge Update beim Start (ignoriert Cache)
FORCE_LIST_UPDATE=false
```

### Lokale Listen bearbeiten

#### Whitelist (`data/lists/whitelist.txt`)
```bash
# Vertrauenswürdige Absender (werden NIE als Spam markiert)

# Komplette E-Mail-Adressen
admin@example.com
newsletter@company.de

# Ganze Domains (alle E-Mails von dieser Domain)
# WICHTIG: Subdomains (z.B. marketing.trusted-company.com) werden NICHT automatisch erkannt!
# Dies ist ein Sicherheitsfeature, um Spam von gekaperten Subdomains zu verhindern.
# Subdomains müssen separat hinzugefügt werden.
trusted-company.com
@trusted-company.com  # Alternative Schreibweise (wird automatisch erkannt)
partner-domain.de
```

#### Blacklist (`data/lists/blacklist.txt`)
```bash
# Bekannte Spam-Absender (werden IMMER als Spam markiert)

# Komplette E-Mail-Adressen
spam@badsite.com
phishing@scam.net

# Ganze Domains
known-spam-domain.xyz
scammer.ru
```

### Externe Blacklists

Automatisch geladen werden (wenn `USE_LISTS=true`):

| Quelle | Typ | Beschreibung | Update-Intervall |
|--------|-----|--------------|------------------|
| **Spamhaus DROP** | IP | Don't Route Or Peer List | Konfigurierbar |
| **Blocklist.de** | IP | Umfassende IP-Blacklist | Konfigurierbar |

**Cache-Speicherort**: `data/lists/` (z.B. `spamhaus_drop.txt`, `blocklist_de.txt`)

### Funktionsweise

```
┌─────────────────────────────────────────────────────┐
│              Eingehende E-Mail                      │
│         (Absender: unknown@example.com)             │
└─────────────────────────────────────────────────────┘
                        ↓
         ┌──────────────────────────────┐
         │   1. WHITELIST CHECK          │
         │   Ist Absender/Domain in      │
         │   whitelist.txt?              │
         └──────────────────────────────┘
                  ↓ JA                ↓ NEIN
         ✅ HAM (kein Spam)            ↓
         └─ FERTIG              ┌──────────────────────────────┐
                                │   2. BLACKLIST CHECK          │
                                │   Ist Absender/Domain in      │
                                │   blacklist.txt oder externe  │
                                │   Listen?                     │
                                └──────────────────────────────┘
                                     ↓ JA                ↓ NEIN
                            🚫 SPAM                      ↓
                            └─ FERTIG           ┌──────────────────────────────┐
                                                │   3. TLD-CHECK                │
                                                │   Verdächtige Sender-TLD?     │
                                                │   (.xyz .top .click .shop …)  │
                                                └──────────────────────────────┘
                                                         ↓ JA            ↓ NEIN
                                                🚫 SPAM                   ↓
                                                └─ FERTIG    ┌─────────────────────┐
                                                             │  4–5. AUTH + DNSBL  │
                                                             │  SPF/DKIM + IP-Check│
                                                             └─────────────────────┘
                                                                      ↓ NEIN
                                                             ┌──────────────────────────────┐
                                                             │   6. LLM-ANALYSE              │
                                                             │   gemma3:12b / ministral3:14b │
                                                             │   SPAM / PHISHING /           │
                                                             │   COMMERCIAL / HAM            │
                                                             └──────────────────────────────┘
```

### Listen verwalten

#### Listen manuell aktualisieren
```bash
# ListManager im Test-Modus starten
python src/list_manager.py
```

#### Listen erzwingen beim Start
```bash
# .env setzen
FORCE_LIST_UPDATE=true
```

#### Cache löschen (komplettes Neu-Download)
```bash
rm -rf data/lists/external/*.txt data/lists/external/metadata.json
```

### Statistiken anzeigen

```python
from src.list_manager import get_list_manager

manager = get_list_manager()
stats = manager.get_stats()

print(f"Whitelist: {stats['whitelist']['total']} Einträge")
print(f"Blacklist: {stats['blacklist']['total']} Einträge")
print(f"Cache: {stats['cache']['directory']}")
```

### Best Practices

#### ✅ DO
- Füge vertrauenswürdige Newsletter zur Whitelist hinzu
- Pflege die Blacklist mit wiederholten Spam-Absendern
- Nutze Domains statt einzelner E-Mails (flexibler)
- Prüfe regelmäßig die Listen auf Duplikate
- Aktiviere `FORCE_LIST_UPDATE=true` nach längerer Inaktivität

#### ❌ DON'T
- Niemals fremde Domains blind zur Whitelist hinzufügen
- Nicht zu viele Einträge in lokalen Listen (Performance)
- Cache nicht manuell editieren (wird überschrieben)
- Externe Listen nicht direkt bearbeiten

### Troubleshooting

#### Listen werden nicht geladen
```bash
# Prüfe Logs
tail -f ~/spam_filter.log | grep -i "list"

# Prüfe Konfiguration
python -c "from src.config import USE_LISTS, LISTS_CACHE_DIR; print(f'USE_LISTS={USE_LISTS}, CACHE={LISTS_CACHE_DIR}')"
```

#### Externe Listen Download fehlgeschlagen
- Cache wird verwendet (falls vorhanden)
- Fehler wird geloggt, Script läuft weiter
- Manueller Download möglich: `python src/list_manager.py`

#### E-Mail trotz Whitelist als Spam markiert
- Prüfe exakte Schreibweise (Groß-/Kleinschreibung wird ignoriert)
- Prüfe Domain-Extraktion: `@domain.com` muss als `domain.com` in Liste sein
- Prüfe Logs für `"Hard Filter"` Einträge

---

### 4. Template-Dateien (mit `.example`)

#### `accounts.yaml.example`
**Zweck**: Vorlage für `accounts.yaml`  
**Versionierung**: ✅ IN Git (ohne echte Passwörter)  

**Verwendung**:
```bash
cp accounts.yaml.example accounts.yaml
# Dann accounts.yaml anpassen
```

#### `.env.example`
**Zweck**: Vorlage für `.env`  
**Versionierung**: ✅ IN Git  

**Verwendung**:
```bash
cp .env.example .env
# Dann .env anpassen
```

---

## Konfigurationshierarchie

```
┌─────────────────────────────────────┐
│         accounts.yaml               │
│  ┌─────────────────────────────┐   │
│  │ Account 1 (enabled: true)   │   │ ← Wird verarbeitet
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ Account 2 (enabled: false)  │   │ ← Wird übersprungen
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ Account 3 (enabled: true)   │   │ ← Wird verarbeitet
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
                 ↓
        Script lädt Config
                 ↓
┌─────────────────────────────────────┐
│          config/settings.yaml       │
│  • mode = days                      │ ← Gilt für ALLE Accounts
│  • days_back = 30                   │
└─────────────────────────────────────┘
```

**Pro Account**: Server, User, Password, Spam-Ordner  
**Global**: Filter-Modus, LLM-Modell, Log-Pfad

---

## Typische Konfigurationen

### Setup 1: Ein Account, letzte 20 E-Mails
**accounts.yaml**:
```yaml
accounts:
  - name: "Hauptaccount"
    user: "max@gmx.de"
    # ... weitere Felder
    enabled: true
```

**config/settings.yaml** (filter-Sektion):
```yaml
filter:
  mode: "count"
  limit: 20
```

---

### Setup 2: Drei Accounts, letzte 7 Tage
**accounts.yaml**:
```yaml
accounts:
  - name: "GMX"
    # ...
    enabled: true
  - name: "Gmail"
    # ...
    enabled: true
  - name: "Outlook"
    # ...
    enabled: true
```

**config/settings.yaml** (filter-Sektion):
```yaml
filter:
  mode: "days"
  days_back: 7
```

---

### Setup 3: Fünf Accounts, nur zwei aktiv
**accounts.yaml**:
```yaml
accounts:
  - name: "Wichtig 1"
    enabled: true     # ← wird verarbeitet
  - name: "Wichtig 2"
    enabled: true     # ← wird verarbeitet
  - name: "Urlaub"
    enabled: false    # ← deaktiviert
  - name: "Alt"
    enabled: false    # ← deaktiviert
  - name: "Test"
    enabled: false    # ← deaktiviert
```

---

## Best Practices

### ✅ DO
- Nutze `enabled: false` statt Accounts zu löschen
- Gib Accounts sprechende Namen (z.B. "Arbeit", "Privat")
- Sichere `accounts.yaml` verschlüsselt
- Teste neue Accounts mit `LIMIT=5` erst

### ❌ DON'T
- Niemals `accounts.yaml` oder `.env` in Git committen
- Keine Klartext-Passwörter in Kommentare schreiben
- Nicht mehrere `accounts.yaml` Dateien anlegen

---

## Validierung

### Config testen ohne E-Mails abzurufen:
```bash
python -c "from src.config import EMAIL_ACCOUNTS; print(f'{len(EMAIL_ACCOUNTS)} aktive Accounts'); [print(f'  - {a[\"name\"]}') for a in EMAIL_ACCOUNTS]"
```

### YAML-Syntax prüfen:
```bash
python -c "import yaml; yaml.safe_load(open('accounts.yaml'))"
```

Kein Output = ✅ Syntax OK  
Fehler = ❌ Syntax-Problem (meist Einrückung)

---

## Sicherheit

### accounts.yaml Berechtigungen
```bash
# Nur Owner kann lesen/schreiben
chmod 600 accounts.yaml
```

### Verschlüsseltes Backup
```bash
# Mit GPG verschlüsseln
gpg -c accounts.yaml
# Erstellt: accounts.yaml.gpg (verschlüsselt)
```

### Umgebungsvariablen (Alternative)
Falls du Passwörter nicht in Dateien speichern willst, kannst du sie auch als Umgebungsvariablen übergeben (erfordert Code-Anpassung).

---

## Hintergrund: Warum .txt Format für Listen?

Wir verwenden bewusst einfache `.txt` Dateien für Whitelist und Blacklist.

### ✅ Vorteile

1. **Universelle Kompatibilität**: Funktioniert auf allen Betriebssystemen und mit jedem Editor.
2. **Einfachheit**: Ein Eintrag pro Zeile. Keine komplexe Syntax wie JSON oder YAML.
3. **Performance**: Sehr schnelles Parsing und minimaler Speicherbedarf.
4. **Git-Freundlichkeit**: Exzellente Diffs (Zeile für Zeile) und einfache Merge-Konflikte.
5. **Industriestandard**: Auch `hosts` Dateien, `robots.txt` und Ad-Blocker nutzen dieses Format.

### 📋 Beispiel

```txt
# Kommentar: Wichtige Kunden
admin@example.com
company.com
```

Im Vergleich zu JSON oder YAML ist dies deutlich robuster gegen Syntaxfehler und einfacher zu warten.
