# E-Mails exportieren: Anleitung für alle Provider

Diese Anleitung zeigt dir wie du E-Mails als `.eml` Dateien aus verschiedenen E-Mail-Providern exportierst. Die `.eml` Dateien brauchst du um den Bayesian Filter zu trainieren.

---

## 📋 Was du brauchst

- Zugang zu deinem E‑Mail‑Account (Webmail oder E‑Mail‑Client)
- Mindestens 100 Spam‑Mails und 100 echte Mails
- Ordner auf deinem Computer: `data/training/spam/` und `data/training/ham/`

---

## 🚀 Automatischer Export (Empfohlen!)

**Am einfachsten:** Nutze die eingebauten Export-Befehle:

```bash
# Exportiert automatisch aus deinem IMAP Spam-Ordner
make export-spam

# Exportiert aus Postausgang (Sent) + Posteingang (nur Whitelist-Absender)
make export-ham
```

**Vorteil:** Schnell, keine GUI-Navigation nötig, funktioniert mit allen IMAP-Providern.

Wenn das funktioniert, musst du die manuellen Anleitungen unten NICHT lesen!

---

## GMX / Web.de (Webmail)

### Spam-Mails exportieren

1. Gehe zu [gmx.de](https://www.gmx.de) und logge dich ein
2. Klicke auf "Spamverdacht" (linke Sidebar)
3. Wähle eine Spam-Mail aus (Klick auf die Betreffzeile)
4. Klicke oben auf "Weitere" (3 Punkte)
5. Wähle "Als Datei speichern"
6. Format: "E-Mail (*.eml)" auswählen
7. Speichere in `data/training/spam/` mit Namen wie `spam_001.eml`, `spam_002.eml`, etc.
8. Wiederhole für 100 Spam-Mails

**💡 Tipp:** Gehe rückwärts durch die Liste (neueste zuerst), damit du aktuelle Spam-Muster bekommst.

### Echte Mails exportieren

1. Gehe zu "Posteingang" oder "Gesendet"
2. Wähle eine Mail aus
3. Klicke auf "Weitere" → "Als Datei speichern"
4. Format: "E-Mail (*.eml)"
5. Speichere in `data/training/ham/` mit Namen wie `ham_001.eml`, `ham_002.eml`, etc.
6. Wiederhole für 100 echte Mails

**⚠️ Wichtig:** Nur ECHTE Mails exportieren - keine Newsletter! (siehe unten)

---

## Gmail (Webmail)

### Spam-Mails exportieren

1. Gehe zu [mail.google.com](https://mail.google.com) und logge dich ein
2. Klicke auf "Spam" (linke Sidebar, evtl. unter "Mehr")
3. Öffne eine Spam-Mail (Klick auf die Betreffzeile)
4. Klicke oben rechts auf "⋮" (3 Punkte)
5. Wähle "Original anzeigen"
6. In dem neuen Tab: Klicke auf "Original herunterladen"
7. Die Datei wird als `.eml` heruntergeladen
8. Verschiebe sie nach `data/training/spam/` und benenne sie um (z.B. `spam_001.eml`)
9. Wiederhole für 100 Spam-Mails

**💡 Tipp:** Gmail löscht Spam nach 30 Tagen automatisch. Exportiere also rechtzeitig!

### Echte Mails exportieren

1. Gehe zu "Posteingang" oder "Gesendet"
2. Öffne eine Mail
3. Klicke auf "⋮" → "Original anzeigen" → "Original herunterladen"
4. Verschiebe nach `data/training/ham/` und benenne um (z.B. `ham_001.eml`)
5. Wiederhole für 100 echte Mails

---

## Outlook / Microsoft 365 (Webmail)

### Spam-Mails exportieren

1. Gehe zu [outlook.com](https://outlook.com) und logge dich ein
2. Klicke auf "Junk-E-Mail" (linke Sidebar)
3. Öffne eine Spam-Mail
4. Klicke oben auf "⋯" (Weitere Aktionen)
5. Wähle "Herunterladen"
6. Die Mail wird als `.eml` Datei gespeichert
7. Verschiebe nach `data/training/spam/` und benenne um
8. Wiederhole für 100 Spam-Mails

### Echte Mails exportieren

1. Gehe zu "Posteingang" oder "Gesendete Elemente"
2. Öffne eine Mail
3. Klicke auf "⋯" → "Herunterladen"
4. Verschiebe nach `data/training/ham/` und benenne um
5. Wiederhole für 100 echte Mails

---

## Thunderbird (E-Mail-Client)

Thunderbird ist ein kostenloser E-Mail-Client der .eml Export sehr einfach macht!

### Installation (falls nicht installiert)

- Download: [thunderbird.net](https://www.thunderbird.net/)
- Richte dein E-Mail-Konto ein (IMAP)

### Mails exportieren

1. Öffne Thunderbird
2. Gehe zum Spam-Ordner (oder Posteingang)
3. Wähle 100 Mails aus (Shift+Klick für Bereich)
4. Rechtsklick → "Nachrichten speichern als" → "Datei"
5. Wähle Ziel-Ordner (`data/training/spam/` oder `data/training/ham/`)
6. Thunderbird speichert alle als `.eml` Dateien

**Vorteil:** Du kannst viele Mails auf einmal exportieren!

---

## Apple Mail (macOS)

### Mails exportieren

1. Öffne Apple Mail
2. Gehe zum Spam-Ordner (oder Posteingang)
3. Wähle eine Mail aus
4. Menü: "Ablage" → "Sichern unter..."
5. Format: "Rohes Nachrichtenformat (.eml)"
6. Speichere in `data/training/spam/` oder `data/training/ham/`
7. Wiederhole für 100 Mails

**💡 Tipp:** Du kannst mehrere Mails markieren (Cmd+Klick) und dann "Ablage" → "Sichern unter..." für alle auf einmal.

---

## 🚨 WICHTIG: Was ist Spam und was NICHT?

**Bevor du exportierst, lies das aufmerksam:**

### ✅ DAS IST SPAM (exportiere nach `spam/`)

- Lotto-Gewinn-Mails ("Sie haben gewonnen!")
- Gefälschte Bank-/PayPal-Mails
- Viagra/Pillen-Werbung
- Investment-Scams
- Phishing-Mails

### ❌ DAS IST KEIN SPAM (exportiere nach `ham/`)

- Newsletter von echten Firmen (Zalando, IKEA, LinkedIn, GitHub)
- Benachrichtigungen (Facebook, Twitter)
- Firmenmails (Arbeit, Rechnungen)
- Mails von Freunden/Familie

**Warum ist das wichtig?**

Wenn du Newsletter als SPAM exportierst:
→ Filter lernt "zalando.de = SPAM"  
→ Filter blockiert ALLE Mails von Zalando (auch Bestellbestätigungen!)

**Lösung für nervige Newsletter:**  
Nutze den Abmelde-Link (am Ende jeder Newsletter-Mail)

---

## 📁 Datei-Benennung

**Gute Benennung** (empfohlen):
```
spam_001.eml
spam_002.eml
...
spam_100.eml

ham_001.eml
ham_002.eml
...
ham_100.eml
```

**Auch OK:**
```
lottery_scam.eml
phishing_paypal.eml
viagra_spam.eml

github_notification.eml
work_email.eml
friend_mail.eml
```

**Nicht so gut:**
```
Mail 1.eml    # Leerzeichen können Probleme machen
spam.eml      # Zu generisch, schwer zu verwalten
```

---

## ✅ Prüfen ob es funktioniert hat

Nach dem Export:

```bash
# Prüfe ob Dateien vorhanden sind
ls data/training/spam/*.eml | wc -l
# Sollte Anzahl der Spam-Mails zeigen

ls data/training/ham/*.eml | wc -l
# Sollte Anzahl der HAM-Mails zeigen
```

**Wenn alles klappt:**
```bash
make train
```

---

## 🆘 Probleme?

### "Keine .eml Dateien gefunden"

**Lösung:** Die Dateien sind nicht im richtigen Ordner  
→ Prüfe: Liegen sie wirklich in `data/training/spam/` bzw. `data/training/ham/`?  
→ Sind sie als `.eml` gespeichert? (nicht `.msg` oder `.txt`)

### Outlook speichert als .msg statt .eml

**Lösung:**  
1. Nutze Outlook Webmail statt Desktop-Client (speichert als .eml)
2. ODER: Konvertiere .msg zu .eml mit Tool `msgconvert` (Linux/Mac)
3. ODER: Nutze automatischen Export: `make export-spam`

### Gmail App-Passwort funktioniert nicht

**Lösung:**  
1. Stelle sicher dass 2-Faktor-Authentifizierung aktiviert ist
2. Gehe zu [Google Account Security](https://myaccount.google.com/security)
3. Erstelle ein neues App-Passwort
4. Nutze das App-Passwort in `accounts.yaml` (nicht dein normales Passwort)

---

## 📚 Nächste Schritte

Nach erfolgreichem Export:

1. **Training starten:**
   ```bash
   make train
   ```

2. **Training-Statistiken prüfen:**
   ```bash
   make train-stats
   ```

3. **Filter starten:**
   ```bash
   make start
   ```

**Weitere Hilfe:**  
→ [docs/GETTING_STARTED.md](GETTING_STARTED.md) - Komplette Einsteiger-Anleitung  
→ [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Problemlösungen
