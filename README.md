# Ollama Spam Guard

🛡️ Automatische E-Mail-Spam-Filterung mit lokalem LLM via Ollama – 100% privat, keine Cloud.

> IMAP-basierter Spam-Filter powered by `ministral-3:14b` für intelligente, lokale E-Mail-Klassifizierung.

## Features

- ✅ **Multi-Account Support**: Mehrere E-Mail-Konten gleichzeitig verwalten
- ✅ **Lokale Spam-Erkennung**: Keine Cloud, 100% lokal via Ollama
- ✅ **3-Stufen-Filter**: Whitelist → Blacklist → LLM-Analyse
- ✅ **Externe Blacklists**: Automatisches Laden von Spamhaus, Blocklist.de etc.
- ✅ **IMAP-Support**: All-Inkl, Gmail, GMX, Outlook, HostEurope, Berlin.de, etc.
- ✅ **LLM-basiert**: Nutzt `ministral-3:14b` (14B Parameter) für höchste Präzision
- ✅ **YAML-Konfiguration**: Übersichtliche Account-Verwaltung
- ✅ **Flexible Filter**: Nach Anzahl oder Zeitraum (letzte X Tage)
- ✅ **Benchmark-Tool**: Teste und vergleiche verschiedene LLM-Modelle (inkl. Reasoning-Support)
- ✅ **Detailliertes Logging**: Vollständige Nachverfolgbarkeit

## Quick Start

```bash
# Repository klonen oder ZIP herunterladen
git clone <your-repo-url> ollama-spam-guard
cd ollama-spam-guard
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

# accounts.yaml anlegen
cp accounts.yaml.example accounts.yaml

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

### 4. Ollama & LLM-Modell
```bash
# Ollama starten
ollama serve

# Modell installieren (Empfehlung: Ministral 3 14B)
ollama pull ministral-3:14b
```

💡 **Modellauswahl**: Siehe [Modellübersicht in SETUP.md](docs/SETUP.md#modellauswahl) für eine vollständige Übersicht aller verfügbaren Modelle mit Empfehlungen basierend auf deiner Hardware.

### 5. Verbindung testen & Filter starten

**Per Doppelklick (macOS):**
Einfach die Datei `start_spam_guard.command` im Projektordner doppelklicken.

**Mit Makefile (empfohlen):**
```bash
make start              # Spam-Filter starten
make spam <adresse>     # Als Spam markieren (Blacklist)
make unspam <adresse>   # Kein Spam (Whitelist + Wiederherstellen)
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

## Konfiguration

### Script-Einstellungen (`.env`)
```bash
# LLM-Modell
SPAM_MODEL=qwen2.5:14b-instruct

# Filter-Modus
FILTER_MODE=count  # oder "days"
LIMIT=50           # Anzahl E-Mails
DAYS_BACK=7        # Tage zurück

# Blacklist/Whitelist System
USE_LISTS=true                # Aktiviert Listen-basierte Filterung
LIST_UPDATE_INTERVAL=24       # Update-Intervall für externe Listen (Stunden)
WHITELIST_FILE=data/lists/whitelist.txt
BLACKLIST_FILE=data/lists/blacklist.txt
```

### E-Mail-Accounts (`accounts.yaml`)
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

Das System verwendet einen **3-Stufen-Ansatz**:

```
1. WHITELIST → E-Mail IMMER als HAM (kein Spam)
   ↓ nicht gefunden
2. BLACKLIST → E-Mail IMMER als SPAM
   ↓ nicht gefunden  
3. LLM-ANALYSE → Intelligente Bewertung mit qwen2.5:14b-instruct
```

**Priorität**: Whitelist > Blacklist > LLM

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

### Modus "count"
Analysiert die letzten X E-Mails (neueste zuerst):
```bash
FILTER_MODE=count
LIMIT=50
```

### Modus "days"
Analysiert alle E-Mails der letzten X Tage:
```bash
FILTER_MODE=days
DAYS_BACK=7
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
| Schwach (bis 8GB) | qwen2.5:1.5b | ~1GB |
| Mittel (8-16GB) | qwen2.5:7b | ~5GB |
| Stark (16GB+) | qwen2.5:14b-instruct | ~9GB |
