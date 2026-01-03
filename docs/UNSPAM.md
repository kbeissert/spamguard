# Spam-Wiederherstellung mit Unspam

## Übersicht

Das **Unspam-Tool** hilft dabei, fälschlich als Spam markierte E-Mails wiederherzustellen. Es durchsucht alle konfigurierten Spam-Ordner nach E-Mails von Absendern, die auf der Whitelist stehen, und verschiebt diese zurück in den Posteingang.

## Warum ist das nützlich?

Trotz intelligenter Filter können manchmal wichtige E-Mails fälschlich als Spam markiert werden. Statt manuell durch Spam-Ordner zu suchen, automatisiert Unspam diesen Prozess.

## Workflow

### 1. Spam-Filter ausführen

```bash
make start
```

Nach der Verarbeitung siehst du eine **Spam-Absender-Übersicht**:

```
════════════════════════════════════════════════════════════
🚫 SPAM-ABSENDER ÜBERSICHT (12 E-Mails verschoben)
════════════════════════════════════════════════════════════

📧 newsletter@marketing-firma.com (3 E-Mail(s))
   • Sonderangebot nur für Sie!
   • Last Chance: 50% Rabatt
   • Verpassen Sie nicht...

📧 info@legitime-firma.de (2 E-Mail(s))
   • Ihre Rechnung für November 2025
   • Wichtige Mitteilung

💡 TIPP: Falls eine E-Mail-Adresse fälschlich blockiert wurde:
   1. Stelle sie wieder her: make unspam <adresse>
════════════════════════════════════════════════════════════
```

### 2. Whitelist aktualisieren & Wiederherstellen

Falls du siehst, dass `info@legitime-firma.de` fälschlich blockiert wurde, kannst du sie mit einem Befehl zur Whitelist hinzufügen und sofort wiederherstellen:

```bash
# Einzelne Adresse
make unspam info@legitime-firma.de

# Oder die ganze Domain (inkl. aller Subdomains)
make unspam legitime-firma.de
```

### 3. Manuelle Wiederherstellung (Interaktiv)

Wenn du keine Adresse angibst, startet der interaktive Modus (stellt alle Mails von Whitelist-Absendern wieder her):

#### Interaktiver Modus (Standard)
```bash
python scripts/unspam.py
```

Das Tool zeigt dir alle gefundenen E-Mails und fragt nach Bestätigung:

```
✅ Gefunden: info@legitime-firma.de
   Betreff: Ihre Rechnung für November 2025
   Grund: Whitelist: info@legitime-firma.de

📊 2 E-Mail(s) von Whitelist-Absendern gefunden

❓ Diese E-Mails in den Posteingang verschieben?
   [J]a / [N]ein / [A]lle Accounts: 
```

#### Automatischer Modus
```bash
python scripts/unspam.py --auto
```

Stellt alle gefundenen E-Mails ohne Nachfrage wieder her.

#### Dry-Run (nur anzeigen)
```bash
python scripts/unspam.py --dry-run
```

Zeigt nur, was verschoben würde, ohne tatsächlich Änderungen vorzunehmen.

## Verwendungsszenarien

### Szenario 1: Newsletter fälschlich blockiert

1. Newsletter landet im Spam
2. Du siehst den Absender in der Spam-Übersicht
3. Füge ihn zur Whitelist hinzu
4. Führe `make unspam` aus
5. Newsletter ist zurück im Posteingang
6. Zukünftige Newsletter landen automatisch im Posteingang

### Szenario 2: Wichtige Geschäftsmail verpasst

1. Nach `make run` siehst du in der Spam-Übersicht: `rechnung@wichtig.de`
2. Erkennst den wichtigen Absender
3. Whitelist aktualisieren: `echo "wichtig.de" >> data/lists/whitelist.txt`
4. `make unspam` → E-Mail zurück im Posteingang
5. Alle weiteren E-Mails von dieser Domain werden nie mehr als Spam markiert

### Szenario 3: Regelmäßige Überprüfung

```bash
# Einmal pro Woche: Prüfe was wiederhergestellt werden könnte
make unspam-dry

# Falls etwas gefunden wird, Whitelist aktualisieren und wiederherstellen
make unspam
```

## Kommandoübersicht

| Befehl | Beschreibung | Verwendung |
|--------|--------------|------------|
| `make unspam` | Interaktiv: fragt nach Bestätigung | Standard-Nutzung |
| `make unspam-auto` | Automatisch: keine Nachfrage | Cron-Jobs, Scripts |
| `make unspam-dry` | Dry-Run: nur anzeigen | Vorschau, Testen |
| `python unspam.py --help` | Hilfe anzeigen | Detaillierte Optionen |

## Wie funktioniert es?

1. **Verbindung**: Verbindet zu jedem konfigurierten E-Mail-Account
2. **Spam-Ordner öffnen**: Öffnet den konfigurierten Spam-Ordner
3. **Durchsuchen**: Prüft jede E-Mail gegen die Whitelist
4. **Wiederherstellen**: Verschiebt gefundene E-Mails zurück in INBOX
5. **Cleanup**: Löscht E-Mails aus Spam-Ordner

## Sicherheit

- ✅ **Nur Whitelist-Absender** werden verschoben
- ✅ **Kein automatisches Löschen** aus Spam
- ✅ **Dry-Run-Modus** zum Testen
- ✅ **Logging** aller Aktionen in `~/spam_filter.log`
- ✅ **Interaktiver Modus** verhindert versehentliche Massenaktionen

## Tipps & Best Practices

### Whitelist effektiv nutzen

```bash
# E-Mail-Adresse (exakt)
admin@firma.de

# Ganze Domain (alle E-Mails dieser Domain)
firma.de
trusted-company.com
```

**Vorteil Domains**: Erfasst alle E-Mails der Firma, nicht nur eine Adresse.

### Regelmäßige Überprüfung

Richte einen wöchentlichen Check ein:

```bash
# Crontab
0 9 * * 1 cd /path/to/ollama-spam-guard && make unspam-dry | mail -s "Unspam Report" deine@email.de
```

### Dokumentiere deine Whitelist

```bash
# data/lists/whitelist.txt mit Kommentaren
# Firma Newsletter
newsletter@firma.de

# Rechnungen
buchhaltung@firma.de

# Partner-Unternehmen (alle E-Mails)
partner-firma.com
```

## Troubleshooting

### "Spam-Ordner nicht gefunden"

**Problem**: Spam-Ordner-Name in `accounts.yaml` ist falsch.

**Lösung**: 
```bash
# Prüfe verfügbare Ordner
make folders

# Aktualisiere accounts.yaml mit korrektem Namen
spam_folder: "Junk"  # oder "Spam", "Spamverdacht", etc.
```

### "Keine E-Mails gefunden"

**Mögliche Ursachen**:
1. Whitelist ist leer → Füge Einträge hinzu
2. Spam-Ordner ist leer → Alles gut!
3. Whitelist-Absender sind nicht im Spam → Alles gut!

### E-Mails werden nicht verschoben

**Prüfe Logs**:
```bash
tail -f ~/spam_filter.log | grep -i "unspam\|wiederhergestellt"
```

**Berechtigungen prüfen**:
- IMAP-Account muss Schreibrechte haben
- Spam-Ordner muss existieren

## Beispiel-Session

```bash
$ make run
[...Spam-Filter läuft...]

🚫 SPAM-ABSENDER ÜBERSICHT (5 E-Mails verschoben)
════════════════════════════════════════════════

📧 newsletter@wichtig.de (2 E-Mail(s))
   • Monats-Update November
   • Wichtige Änderungen

💡 TIPP: Whitelist aktualisieren und make unspam ausführen
════════════════════════════════════════════════

$ echo "newsletter@wichtig.de" >> data/lists/whitelist.txt

$ make unspam
♻️  Starte Unspam...

📬 Account 1/2: Mein Account
────────────────────────────

✅ Gefunden: newsletter@wichtig.de
   Betreff: Monats-Update November
   Grund: Whitelist: newsletter@wichtig.de

✅ Gefunden: newsletter@wichtig.de
   Betreff: Wichtige Änderungen
   Grund: Whitelist: newsletter@wichtig.de

📊 2 E-Mail(s) von Whitelist-Absendern gefunden

❓ Diese E-Mails in den Posteingang verschieben?
   [J]a / [N]ein / [A]lle Accounts: j

🔄 Stelle 2 E-Mail(s) wieder her...

✅ Wiederhergestellt: newsletter@wichtig.de
   Betreff: Monats-Update November

✅ Wiederhergestellt: newsletter@wichtig.de
   Betreff: Wichtige Änderungen

✅ 2 von 2 E-Mail(s) wiederhergestellt

📊 ZUSAMMENFASSUNG
════════════════════
   Accounts geprüft: 2
   E-Mails gefunden: 2
   Wiederhergestellt: 2
════════════════════

✅ E-Mails erfolgreich wiederhergestellt!
💡 TIPP: Prüfe deinen Posteingang in deinem E-Mail-Programm
```

## Integration in Workflows

### Tägliche Spam-Filterung + Wiederherstellung

```bash
#!/bin/bash
# daily-spam-check.sh

cd /path/to/ollama-spam-guard

# 1. Spam-Filter ausführen
make run

# 2. Automatisch Whitelist-E-Mails wiederherstellen
make unspam-auto

# 3. Report senden
echo "Spam-Filter und Wiederherstellung abgeschlossen" | mail -s "Spam Report" admin@example.com
```

### Cron-Job (täglich um 6 Uhr morgens)

```bash
0 6 * * * /path/to/daily-spam-check.sh >> /var/log/spam-guard.log 2>&1
```

## Weitere Informationen

- 📖 [README.md](../README.md) - Hauptdokumentation
- 🔧 [CONFIGURATION.md](CONFIGURATION.md) - Whitelist/Blacklist Konfiguration
- ⚠️ [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Problemlösungen
