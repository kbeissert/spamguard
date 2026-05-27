# Listen-Audit: Interaktive Listenverwaltung

## Übersicht

Das **Audit-Tool** ermöglicht es, Whitelist und Blacklist interaktiv zu durchsuchen und direkt aus der Übersicht heraus Einträge zu bearbeiten — ohne die Dateien manuell öffnen zu müssen. Wenn eine Liste über die Zeit gewachsen ist und viele Einträge enthält, bietet der Audit-Modus eine strukturierte Möglichkeit, die Listen zu bereinigen und gleichzeitig fälschlich blockierte Mails wiederherzustellen.

---

## Aufruf

### Mit Makefile (empfohlen)

```bash
make audit              # Fragt interaktiv welche Liste
make audit-whitelist    # Startet direkt mit der Whitelist
make audit-blacklist    # Startet direkt mit der Blacklist
```

### Direkt mit Python

```bash
python scripts/audit_lists.py              # Fragt welche Liste
python scripts/audit_lists.py --whitelist  # Direkt Whitelist
python scripts/audit_lists.py --blacklist  # Direkt Blacklist
```

---

## Die drei Modi

### Modus 1: Listenauswahl (Standard)

Wird `make audit` ohne weitere Argumente gestartet, fragt das Tool zunächst welche Liste geprüft werden soll. Die aktuelle Anzahl der Einträge wird dabei direkt angezeigt:

```
╔══════════════════════════════════════════════════════╗
║              Spam Guard — Listen Audit               ║
╚══════════════════════════════════════════════════════╝

  Welche Liste prüfen?
  [W]  Whitelist  (12 Einträge)
  [B]  Blacklist  (34 Einträge)
  [A]  Beide

  Auswahl:
```

- **W** — öffnet die Whitelist
- **B** — öffnet die Blacklist
- **A** — beide Listen nacheinander (erst Whitelist, dann Blacklist)

### Modus 2: Direktstart Whitelist

```bash
make audit-whitelist
```

Überspringt die Listenauswahl und öffnet sofort die Whitelist. Sinnvoll nach einem Spam-Filter-Lauf, wenn du gezielt prüfen möchtest ob wichtige Absender falsch konfiguriert sind.

### Modus 3: Direktstart Blacklist

```bash
make audit-blacklist
```

Öffnet direkt die Blacklist. Sinnvoll zur regelmäßigen Pflege — zum Beispiel wenn eine Domain, die früher Spam schickte, jetzt wieder legitim ist und von der Blacklist entfernt oder auf die Whitelist verschoben werden soll.

---

## Einträge auswählen

Nachdem die Liste angezeigt wird, erscheinen alle Einträge nummeriert — E-Mail-Adressen und Domains getrennt aufgelistet:

```
════════════════════════════════════════════════════════
  📋 WHITELIST  (12 Einträge)
════════════════════════════════════════════════════════

  📧  E-Mail-Adressen (4):
      1.  admin@firma.de
      2.  newsletter@wichtig.de
      3.  info@partner.com
      4.  rechnung@shop.de

  🌐  Domains (8):
      5.  trusted-domain.com
      6.  bank.de
      7.  github.com
      ...

════════════════════════════════════════════════════════

  Eintrag auswählen:
  • Nummer eingeben (z.B.  3 )
  • Bereich eingeben (z.B.  1-5 )
  • [A] Alle der Reihe nach durchgehen
  • [Q] Beenden
```

Es gibt drei Auswahlmethoden:

| Eingabe | Bedeutung |
|---------|-----------|
| `3` | Öffnet Eintrag Nummer 3 |
| `1-5` | Geht Einträge 1 bis 5 der Reihe nach durch |
| `A` | Geht alle Einträge der Reihe nach durch |
| `Q` | Beendet den Audit |

---

## Aktionen pro Eintrag

Für jeden ausgewählten Eintrag öffnet sich ein Aktionsmenü:

### Whitelist-Eintrag

```
  ┌────────────────────────────────────────────────────┐
  │  newsletter@wichtig.de                             │
  └────────────────────────────────────────────────────┘

  [R]  Entfernen
  [B]  Zur Blacklist verschieben
  [U]  Unspam: Mails aus Spam-Ordner zurückholen
  [S]  Überspringen
  [Q]  Audit beenden

  Aktion:
```

### Blacklist-Eintrag

```
  ┌────────────────────────────────────────────────────┐
  │  spam-domain.xyz                                   │
  └────────────────────────────────────────────────────┘

  [R]  Entfernen
  [W]  Zur Whitelist verschieben
  [S]  Überspringen
  [Q]  Audit beenden

  Aktion:
```

### Beschreibung der Aktionen

#### [R] Entfernen

Löscht den Eintrag aus der aktuellen Liste. Die Mail-Adresse oder Domain wird beim nächsten Spam-Filter-Lauf nicht mehr berücksichtigt.

```
  ✅  Entfernt: newsletter@wichtig.de
```

#### [B] / [W] Auf andere Liste verschieben

Entfernt den Eintrag aus der aktuellen Liste und fügt ihn zur jeweils anderen Liste hinzu.

- Whitelist-Eintrag → **[B]** verschiebt auf die Blacklist
- Blacklist-Eintrag → **[W]** verschiebt auf die Whitelist

```
  ✅  Verschoben nach Blacklist: newsletter@wichtig.de
```

**Typischer Anwendungsfall:** Eine Domain, die früher vertrauenswürdig war, schickt jetzt Spam. Im Audit mit **[B]** direkt auf die Blacklist verschieben — ohne zwei separate Befehle ausführen zu müssen.

#### [U] Unspam: Mails zurückholen (nur Whitelist)

Verbindet sich zu allen konfigurierten IMAP-Accounts, durchsucht jeden Spam-Ordner nach E-Mails dieses Absenders und verschiebt gefundene Mails zurück in den Posteingang. Der Eintrag bleibt dabei auf der Whitelist — nur die Mails werden wiederhergestellt.

```
  ♻️   Suche Mails von newsletter@wichtig.de in allen Spam-Ordnern...
     ✅  newsletter@wichtig.de: Monats-Update November
     ✅  newsletter@wichtig.de: Wichtige Änderungen

  ✅  2 E-Mail(s) zurückgeholt
```

Wenn keine Mails gefunden werden:

```
  ℹ️   Keine Mails von newsletter@wichtig.de im Spam-Ordner gefunden
```

**Hinweis:** Die Unspam-Funktion unterstützt sowohl exakte E-Mail-Adressen als auch Domains. Ist `wichtig.de` auf der Whitelist, werden alle Mails von `*@wichtig.de` im Spam-Ordner gefunden und wiederhergestellt.

#### [S] Überspringen

Springt zum nächsten Eintrag, ohne Änderungen vorzunehmen. Nützlich beim Durchgehen mit Modus **A** oder einem Bereich, wenn ein Eintrag korrekt ist.

#### [Q] Audit beenden

Beendet den Audit sofort, auch mitten in einem Durchgang.

---

## Vollständiges Beispiel

```bash
$ make audit

╔══════════════════════════════════════════════════════╗
║              Spam Guard — Listen Audit               ║
╚══════════════════════════════════════════════════════╝

  Welche Liste prüfen?
  [W]  Whitelist  (5 Einträge)
  [B]  Blacklist  (12 Einträge)
  [A]  Beide

  Auswahl: w

════════════════════════════════════════════════════════
  📋 WHITELIST  (5 Einträge)
════════════════════════════════════════════════════════

  📧  E-Mail-Adressen (2):
      1.  admin@firma.de
      2.  newsletter@altbekannt.de

  🌐  Domains (3):
      3.  trusted-shop.de
      4.  bank.de
      5.  github.com

════════════════════════════════════════════════════════

  Eintrag auswählen:
  • Nummer eingeben (z.B.  3 )
  • Bereich eingeben (z.B.  1-5 )
  • [A] Alle der Reihe nach durchgehen
  • [Q] Beenden

  Auswahl: 2

  ┌────────────────────────────────────────────────────┐
  │  newsletter@altbekannt.de                          │
  └────────────────────────────────────────────────────┘

  [R]  Entfernen
  [B]  Zur Blacklist verschieben
  [U]  Unspam: Mails aus Spam-Ordner zurückholen
  [S]  Überspringen
  [Q]  Audit beenden

  Aktion: u

  ♻️   Suche Mails von newsletter@altbekannt.de in allen Spam-Ordnern...
     ✅  newsletter@altbekannt.de: November-Update

  ✅  1 E-Mail(s) zurückgeholt

  Auswahl: 5

  ┌────────────────────────────────────────────────────┐
  │  github.com                                        │
  └────────────────────────────────────────────────────┘

  [R]  Entfernen
  [B]  Zur Blacklist verschieben
  [U]  Unspam: Mails aus Spam-Ordner zurückholen
  [S]  Überspringen
  [Q]  Audit beenden

  Aktion: s

  Auswahl: q

  ✅  Audit abgeschlossen.
```

---

## Empfohlene Workflows

### Regelmäßige Listen-Pflege (monatlich)

```bash
# Überblick verschaffen
make show-lists

# Dann gezielt bereinigen
make audit-whitelist
make audit-blacklist
```

### Nach einem Spam-Filter-Lauf

```bash
# 1. Spam-Filter ausführen
make start

# 2. Spam-Übersicht prüfen (wird am Ende des Filters angezeigt)

# 3. Whitelist auf fälschlich blockierte Absender prüfen
make audit-whitelist
# → Für gefundene Absender direkt [U] für Unspam drücken
```

### Alle Einträge in einem Durchgang prüfen

```bash
make audit
# Auswahl: A → Beide Listen
# Dann: A → Alle der Reihe nach durchgehen
```

---

## Unterschied zu anderen Tools

| Tool | Zweck |
|------|-------|
| `make show-lists` | Schnelle Übersicht, keine Aktionen möglich |
| `make unspam <adresse>` | Einzelne Adresse direkt zur Whitelist + Mails zurückholen |
| `make spam <adresse>` | Einzelne Adresse direkt zur Blacklist |
| **`make audit`** | **Interaktive Durchsicht aller Einträge mit Aktionen** |

Das Audit-Tool ergänzt die anderen Befehle: Statt jede Adresse einzeln über die Kommandozeile zu verwalten, kann man die gesamte Liste in einem Durchgang durcharbeiten und direkt reagieren.

---

## Weitere Informationen

- 📖 [README.md](../README.md) — Hauptdokumentation
- ♻️ [UNSPAM.md](UNSPAM.md) — Spam-Wiederherstellung für einzelne Adressen
- 🔧 [CONFIGURATION.md](CONFIGURATION.md) — Whitelist/Blacklist-Konfiguration
