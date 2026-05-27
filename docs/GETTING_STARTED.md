# SpamGuard: Erste Schritte (für Einsteiger)

> **Für wen ist dieser Guide?** Für Leute die "ein bisschen was am Rechner einstellen können" aber keine Entwickler sind. Wenn du Terminal/Kommandozeile öffnen kannst und Ordner erstellen kannst, bist du hier richtig!

---

## 📋 Was du brauchst (5 Minuten Vorbereitung)

Bevor du anfängst, stelle sicher, dass du:

- [ ] Einen E-Mail-Account hast (GMX, Gmail, Outlook, etc.)
- [ ] Dein E-Mail-Passwort kennst
- [ ] Ollama installiert hast ([Anleitung hier](https://ollama.ai))
- [ ] Terminal/Kommandozeile öffnen kannst
- [ ] Python 3.8 oder neuer installiert hast

**Wie prüfe ich, ob Python installiert ist?**
```bash
python --version
# oder
python3 --version
```

Sollte etwas wie `Python 3.10.0` anzeigen. Wenn nicht → Python installieren: https://www.python.org/downloads/

---

## 🚀 In 3 Schritten zum Spam-Filter

### Schritt 1: Installation (10 Minuten)

#### 1.1 Projekt herunterladen

**Option A: Mit Git (wenn installiert)**
```bash
git clone https://github.com/dein-username/spam-guard.git
cd SpamGuard
```

**Option B: Ohne Git**
1. Gehe zur GitHub-Seite des Projekts
2. Klicke auf den grünen "Code" Button
3. Wähle "Download ZIP"
4. Entpacke die Datei in einen Ordner deiner Wahl
5. Öffne Terminal im Projekt-Ordner

#### 1.2 Dependencies installieren

```bash
# Im Projekt-Ordner (dort wo die Datei "Makefile" liegt)
make install
```

**Was passiert jetzt?**  
Das Programm lädt alle benötigten Komponenten herunter (Python-Bibliotheken). Das dauert 2-3 Minuten.

**Wenn "make" nicht funktioniert:**
```bash
python3 -m pip install -e .
```

---

### Schritt 2: Konfiguration (5 Minuten)

#### 2.1 E-Mail-Account einrichten

Erstelle die Datei `config/accounts.yaml` mit folgendem Inhalt:

**Für GMX:**
```yaml
accounts:
  - name: "Mein GMX Account"
    user: "deine-email@gmx.de"
    password: "dein-passwort"
    server: "imap.gmx.net"
    port: 993
    spam_folder: "Spamverdacht"
    enabled: true
```

**Für Gmail:**
```yaml
accounts:
  - name: "Mein Gmail Account"
    user: "deine-email@gmail.com"
    password: "app-spezifisches-passwort"  # Nicht dein normales Passwort!
    server: "imap.gmail.com"
    port: 993
    spam_folder: "[Gmail]/Spam"
    enabled: true
```

**⚠️ Gmail-Hinweis:** Du brauchst ein App-Passwort, nicht dein normales Gmail-Passwort!  
→ [Google-Anleitung: App-Passwort erstellen](https://support.google.com/accounts/answer/185833)

**Für Outlook/Hotmail:**
```yaml
accounts:
  - name: "Mein Outlook Account"
    user: "deine-email@outlook.com"
    password: "dein-passwort"
    server: "outlook.office365.com"
    port: 993
    spam_folder: "Junk"
    enabled: true
```

💡 Tipp: Die Datei `config/accounts.yaml.example` im Projekt enthält weitere Beispiele.

#### 2.2 Ollama starten

**Schritt 1: Ollama-Service starten**
```bash
# In einem separaten Terminal-Fenster:
ollama serve
```

Lass dieses Fenster offen! Ollama muss laufen während der Filter arbeitet.

**Schritt 2: LLM-Modell herunterladen**
```bash
# In einem neuen Terminal-Fenster:
ollama pull gemma3:12b
```

**Was passiert?**  
Das lädt ein KI-Modell herunter (~7 GB). Das dauert 10-20 Minuten je nach Internet-Geschwindigkeit.

**💡 Alternativen:**
- **Kleiner/Schneller:** `ollama pull gemma4:e4b` (~2 GB, weniger genau)
- **Größer/Genauer:** `ollama pull ministral3:14b` (~14 GB, sehr genau)

---

### Schritt 3: Training (15 Minuten)

#### Was ist Training?

**Einfach erklärt:**  
Du zeigst dem Filter Beispiele von Spam und echten E-Mails. Der Filter lernt daraus was Spam ist und was nicht.

**Wie viele E-Mails brauchst du?**

| Anzahl | Ergebnis |
|--------|----------|
| 10 Spam + 10 echte | Funktioniert, aber nicht perfekt (~75% richtig) |
| **100 Spam + 100 echte** | **Sehr gut (~90% richtig)** ⭐ Empfohlen |
| 200+ von jedem | Perfekt (~95% richtig) |

#### 🚨 WICHTIG: Was ist Spam und was NICHT?

Das ist der häufigste Fehler! Bitte lies das aufmerksam:

**✅ DAS IST SPAM** (gehört in `data/training/spam/`):
- Lotto-Gewinn-Mails ("Sie haben 1 Million gewonnen!")
- Gefälschte Bank-Mails ("Ihr Konto wurde gesperrt")
- Viagra/Pillen-Werbung
- Nigeria-Prinz-Betrug
- Investment-Scams ("10.000€ pro Tag verdienen!")
- Phishing-Mails (gefälschte PayPal, Amazon, etc.)

**❌ DAS IST KEIN SPAM** (gehört in `data/training/ham/`):
- Newsletter von echten Firmen (Zalando, IKEA, etc.) - **auch wenn nervig!**
- Benachrichtigungen (LinkedIn, Facebook, Twitter)
- Firmenmails (Arbeit, Rechnungen, Bestellbestätigungen)
- Mails von Freunden/Familie
- GitHub/StackOverflow Notifications

**Warum ist das SO wichtig?**

Wenn du Newsletter als SPAM markierst:
1. Filter lernt: "zalando.de = SPAM"
2. Filter blockt später ALLE Mails von Zalando
3. Du verpasst deine Bestellbestätigungen!

**Das gleiche gilt für:** LinkedIn, GitHub, Facebook, IKEA, Amazon, etc.

**Was wenn ich Newsletter trotzdem loswerden will?**
→ Nutze den Abmelde-Link (steht am Ende jeder Newsletter-Mail)  
→ ODER: Erstelle eine Regel in deinem E-Mail-Programm

#### 3.1 E-Mails exportieren

**Option A: Automatisch (empfohlen)**

```bash
# Exportiert Spam aus deinem Spam-Ordner
make export-spam

# Exportiert echte Mails aus deinem Postausgang
make export-ham
```

**Was passiert?**
- Das Programm verbindet sich mit deinem E-Mail-Account
- Es lädt 500 Spam-Mails herunter und speichert sie in `data/training/spam/`
- Es lädt 200 echte Mails (60% aus deinem Sent-Ordner, 40% aus Posteingang)
- Dauer: 5-10 Minuten

**Option B: Manuell** (wenn automatisch nicht klappt)

1. Gehe zu deinem E-Mail-Provider (GMX.de, Gmail.com, etc.)
2. Öffne den Spam-Ordner
3. Wähle 100 Spam-Mails aus
4. Speichere sie als `.eml` Dateien (bei GMX: "Weitere" → "Als Datei speichern")
5. Kopiere sie nach `data/training/spam/`

Gleich für echte Mails → `data/training/ham/`

💡 **Detaillierte Anleitungen:** Siehe [docs/EMAIL_EXPORT_GUIDE.md](EMAIL_EXPORT_GUIDE.md)

#### 3.2 Training starten

```bash
make train
```

**Was passiert jetzt?**
- Das Programm liest alle `.eml` Dateien
- Es analysiert die Unterschiede zwischen Spam und echten Mails
- Es erstellt ein "Modell" (trainierter Filter) in `data/models/bayesian_model.pkl`
- Dauer: 5-10 Sekunden für 200 Mails

**Ausgabe sieht so aus:**
```
🤖 Training Bayesian Filter...

📂 Lese Training-Daten...
   Spam: 120 Dateien
   HAM:  105 Dateien

✅ Erfolgreich gelesen:
   Spam: 120/120 Dateien
   HAM:  105/105 Dateien

✅ Training abgeschlossen!
   Spam: 120 Mails
   HAM:  105 Mails
   CV Folds: 5
   Features: 1847

💾 Modell gespeichert: data/models/bayesian_model.pkl
```

**Was bedeutet das?**
- **CV Folds 5**: Sehr gut! (2 = wenig Daten, 5 = optimal trainiert)
- **Features 1847**: Der Filter kennt 1847 Wörter/Muster
- **Modell gespeichert**: Der Filter ist jetzt einsatzbereit!

**Wenn du eine Warnung siehst:**
```
⚠️  Hinweis: < 100 Mails pro Kategorie
   Genauigkeit kann < 85% sein
```

Das bedeutet: Du hast zu wenig Mails. Der Filter funktioniert trotzdem, aber macht mehr Fehler. Versuche 100+ Mails pro Kategorie zu sammeln.

---

## ✅ Filter starten

Jetzt bist du fertig mit der Einrichtung! Starte den Filter:

```bash
make start
```

**Was passiert jetzt?**
1. Der Filter verbindet sich mit deinem E-Mail-Account
2. Er liest die neuesten E-Mails aus deinem Posteingang
3. Er prüft jede Mail: Ist das Spam?
4. Wenn ja → verschiebt er die Mail in deinen Spam-Ordner
5. Wenn nein → Mail bleibt im Posteingang

**Du siehst so etwas:**
```
🛡️  Starte Spam-Filter...
✅ Konfiguration geladen
   Ollama: http://localhost:11434 (gemma3:12b)
   🤖 Bayesian Filter: Aktiv (LLM-Fallback: Nein)
   📋 Listen: Aktiv (4 externe Blacklists)

[1/3] Account: Mein GMX Account (max@gmx.de)
   ⚡ Bayesian: HAM (0.123) - notifications@github.com
   ⚡ Bayesian: SPAM (0.923) - winner@lottery-scam.com
   
📊 Zusammenfassung: 2 Mails geprüft, 1 Spam verschoben
```

**Du musst nichts mehr tun!** Der Filter läuft und bewacht deine E-Mails.

**Filter stoppen:** Drücke `Ctrl+C` im Terminal

---

## 🔧 Was wenn etwas nicht funktioniert?

### Problem 1: "No such file or directory: config/accounts.yaml"

**Lösung:** Du hast die Konfigurationsdatei nicht erstellt  
→ Gehe zurück zu **Schritt 2.1**

---

### Problem 2: "Kein Bayesian-Modell gefunden"

**Lösung:** Du hast das Training nicht ausgeführt  
→ Gehe zurück zu **Schritt 3.2** und führe `make train` aus

---

### Problem 3: "Training mit 0 Spam + 0 HAM Mails"

**Lösung:** Du hast keine `.eml` Dateien in `data/training/`  
→ Gehe zurück zu **Schritt 3.1** und exportiere E-Mails

---

### Problem 4: Filter markiert alles als Spam

**Lösung:** Du hast wahrscheinlich Newsletter als Spam trainiert  
→ Lösche `data/models/` komplett:
```bash
rm -rf data/models/
```
→ Überprüfe `data/training/spam/` und `data/training/ham/`  
→ Verschiebe Newsletter nach `ham/`  
→ Führe `make train` neu aus

---

### Problem 5: "Ollama nicht erreichbar"

**Lösung:** Ollama läuft nicht  
→ Öffne ein neues Terminal und starte:
```bash
ollama serve
```

---

**Mehr Hilfe?**  
→ Lies **[docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md)** für detaillierte Lösungen

---

## 📈 Wie gut ist mein Filter?

Nach ein paar Tagen kannst du prüfen wie gut dein Filter trainiert ist:

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

⚠️  Niedrige Datenmenge — Ziel: 100+ Mails pro Kategorie
```

**Was bedeutet das?**
- **Features 1847**: Der Filter kennt 1847 Spam-Muster
- **CV Folds 5**: Optimal trainiert
- **Warnung**: Wenn du < 100 Mails hast, sammle mehr für bessere Genauigkeit

---

## 🔄 Filter verbessern

Der Filter macht Fehler? Das ist normal am Anfang! So verbesserst du ihn:

### Fehler-Typ 1: Echte Mail wurde als Spam markiert (False Positive)

1. Gehe zu deinem Spam-Ordner
2. Finde die falsch markierte Mail
3. Speichere sie als `.eml` Datei
4. Kopiere sie nach `data/training/ham/`
5. Führe `make train` aus

Der Filter lernt jetzt: "Diese Art von Mail ist kein Spam!"

### Fehler-Typ 2: Spam wurde nicht erkannt (False Negative)

1. Finde die Spam-Mail in deinem Posteingang
2. Speichere sie als `.eml` Datei
3. Kopiere sie nach `data/training/spam/`
4. Führe `make train` aus

Der Filter lernt jetzt: "Diese Art von Mail ist Spam!"

**⚠️ WICHTIG:** Die alten `.eml` Dateien NICHT löschen!

Bei jedem `make train` trainiert der Filter auf ALLEN Mails neu. Wenn du alte Mails löschst, "vergisst" der Filter diese Patterns.

---

## ❓ Häufige Fragen

**F: Kann ich den Filter auf mehreren E-Mail-Accounts verwenden?**  
A: Ja! Füge einfach mehrere Accounts in `config/accounts.yaml` hinzu (siehe Beispiel-Datei).

**F: Brauche ich Internet für den Filter?**  
A: Ja, zum Abrufen der E-Mails. Aber der Filter läuft lokal auf deinem PC.

**F: Sieht jemand anderes meine E-Mails?**  
A: Nein! Alles läuft zu 100% lokal auf deinem Computer. Keine Cloud, keine fremden Server, 100% privat.

**F: Kann ich den Filter stoppen?**  
A: Ja, drücke `Ctrl+C` im Terminal-Fenster.

**F: Wie oft sollte ich den Filter laufen lassen?**  
A: So oft du willst! Täglich, mehrmals täglich, oder automatisiert (siehe [docs/SETUP.md](SETUP.md) für Automatisierung).

**F: Was ist wenn ich Newsletter doch loswerden will?**  
A: Dann melde dich vom Newsletter ab (Link am Ende jeder Newsletter-Mail).  
→ Oder: Erstelle eine Regel in deinem E-Mail-Programm die Newsletter automatisch in einen Ordner verschiebt.

**F: Wie lange dauert der Filter pro Mail?**  
A: Mit Bayesian Filter: ~10ms für einfache Mails, ~1,6s wenn LLM gebraucht wird. Im Durchschnitt: 50-60 Mails pro Minute.

**F: Kann ich den Filter auch ohne Training nutzen?**  
A: Ja, aber dann nutzt er nur das LLM (langsamer). Mit Training ist er 2-3x schneller.

---

## 📚 Weiterführende Dokumentation

Wenn du mehr wissen willst:

- **[docs/SETUP.md](SETUP.md)** - Ausführliche Setup-Anleitung mit allen Details
- **[docs/CONFIGURATION.md](CONFIGURATION.md)** - Alle Konfigurations-Optionen erklärt
- **[docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Problemlösungen für alle Fehler
- **[docs/BENCHMARK.md](BENCHMARK.md)** - Verschiedene LLM-Modelle vergleichen
- **[docs/EMAIL_EXPORT_GUIDE.md](EMAIL_EXPORT_GUIDE.md)** - E-Mail-Export für alle Provider

---

## 🎉 Geschafft!

Glückwunsch! Dein Spam-Filter läuft jetzt und lernt mit jeder Mail dazu.

**Tipp für die ersten Tage:**
- Prüfe täglich deinen Spam-Ordner auf False Positives
- Wenn du eine falsch klassifizierte Mail findest → nachtrainieren (siehe "Filter verbessern")
- Nach 1-2 Wochen macht der Filter kaum noch Fehler

**Viel Erfolg! 🚀**
