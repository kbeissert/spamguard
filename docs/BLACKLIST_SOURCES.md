# Externe Blacklist-Quellen für Spam Guard

## Übersicht

Diese Datei dokumentiert verfügbare externe Blacklist-Quellen und erklärt, wie du eigene Quellen hinzufügen kannst.

## 🔧 Eigene Quellen hinzufügen

### Schritt 1: `data/lists/blacklist_sources.yaml` öffnen

Öffne die YAML-Konfigurationsdatei (erstelle sie aus dem Template falls nötig):

```bash
cp data/lists/blacklist_sources.yaml.example data/lists/blacklist_sources.yaml
nano data/lists/blacklist_sources.yaml
```

### Schritt 2: Quelle hinzufügen

Füge einen neuen Eintrag im YAML-Format hinzu:

```yaml
meine_liste:
  url: "https://example.com/spam-list.txt"
  type: "domain"  # ip, ip_cidr, domain oder email
  description: "Beschreibung deiner Liste"
  enabled: true
```

### Schritt 3: Spam-Filter neu starten

Beim nächsten Start (`make run`) wird die neue Quelle automatisch geladen.

## 📋 Unterstützte Typen

| Typ | Beschreibung | Beispiel |
|-----|--------------|----------|
| `ip` | Einzelne IP-Adressen | `192.168.1.1` |
| `ip_cidr` | IP-Bereiche (CIDR) | `192.168.1.0/24` |
| `domain` | Domain-Namen | `spam-domain.com` |
| `email` | E-Mail-Adressen | `spam@example.com` |

## 🌐 Verfügbare Blacklist-Quellen

### Aktiv (Standard)

#### Spamhaus DROP
- **URL**: https://www.spamhaus.org/drop/drop.txt
- **Typ**: IP (CIDR)
- **Beschreibung**: Don't Route Or Peer - Bekannte Spam-Netzwerke
- **Update**: Täglich
- **Größe**: ~1.000 Einträge

#### Blocklist.de
- **URL**: https://lists.blocklist.de/lists/all.txt
- **Typ**: IP
- **Beschreibung**: Aggregierte Liste von Spam-IPs
- **Update**: Stündlich
- **Größe**: ~50.000+ Einträge

### Optional (auskommentiert in `list_manager.py`)

#### Spamhaus EDROP
- **URL**: https://www.spamhaus.org/drop/edrop.txt
- **Typ**: IP (CIDR)
- **Beschreibung**: Extended DROP - Zusätzliche Spam-Netzwerke
- **Größe**: ~500 Einträge

#### Abuse.ch URLhaus
- **URL**: https://urlhaus.abuse.ch/downloads/text/
- **Typ**: Domain
- **Beschreibung**: Malicious URLs und Domains
- **Größe**: ~10.000+ Einträge

#### Matomo Referrer Spam
- **URL**: https://raw.githubusercontent.com/matomo-org/referrer-spam-list/master/spammers.txt
- **Typ**: Domain
- **Beschreibung**: Referrer-Spam Domains (häufig in E-Mails)
- **Größe**: ~1.500 Einträge

#### StopForumSpam - Toxic Domains
- **URL**: https://www.stopforumspam.com/downloads/toxic_domains_whole.txt
- **Typ**: Domain
- **Beschreibung**: Bekannte Spam-Domains aus Foren
- **Größe**: ~5.000 Einträge

#### Firebog - Advertising Domains
- **URL**: https://v.firebog.net/hosts/Easylist.txt
- **Typ**: Domain
- **Beschreibung**: Werbe-Domains (kann auch legitime Newsletter blockieren!)
- **Größe**: ~20.000+ Einträge
- **⚠️ Warnung**: Kann False Positives verursachen

#### Firebog - Malicious Domains
- **URL**: https://v.firebog.net/hosts/Prigent-Malware.txt
- **Typ**: Domain
- **Beschreibung**: Malware-verbreitende Domains
- **Größe**: ~15.000 Einträge

#### Disposable Email Domains
- **URL**: https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/master/disposable_email_blocklist.conf
- **Typ**: Domain
- **Beschreibung**: Wegwerf-E-Mail-Provider (z.B. 10minutemail.com)
- **Größe**: ~20.000+ Einträge
- **⚠️ Warnung**: Blockiert legitime temporäre E-Mail-Dienste

#### SORBS SMTP Spam Sources
- **URL**: http://www.dnsbl.sorbs.net/data/smtp.txt
- **Typ**: IP
- **Beschreibung**: SMTP-Server die Spam versenden
- **Größe**: Variable
- **⚠️ Hinweis**: HTTP (nicht HTTPS)

## 🎯 Empfohlene Konfigurationen

### Minimal (Standard)
Nur die wichtigsten Listen, schnellster Start:
```python
- spamhaus_drop (aktiv)
- blocklist_de (aktiv)
```

### Ausgewogen
Gute Balance zwischen Schutz und Performance:
```python
- spamhaus_drop (aktiv)
- spamhaus_edrop (aktivieren)
- blocklist_de (aktiv)
- abuse_ch_urlhaus (aktivieren)
```

### Maximal
Maximum Protection (kann False Positives verursachen):
```python
- Alle Listen aktivieren
```
**⚠️ Warnung**: Kann legitime E-Mails blockieren!

## 🔍 Eigene Quellen finden

### Kriterien für gute Blacklists:
1. ✅ Regelmäßig aktualisiert (täglich/wöchentlich)
2. ✅ Öffentlich zugänglich (HTTP/HTTPS)
3. ✅ Klares Format (eine Zeile pro Eintrag)
4. ✅ Dokumentiert und vertrauenswürdig
5. ✅ Keine Authentifizierung erforderlich

### Wo finde ich Listen?
- **GitHub**: Suche nach "spam blacklist", "email blacklist"
- **Blocklist Aggregatoren**: Firebog.net, IPsum
- **Security Communities**: SANS ISC, Spamhaus
- **Anti-Spam Projekte**: Apache SpamAssassin, Postfix

### Beispiel-Suche auf GitHub:
```bash
site:github.com "spam blacklist" ".txt"
site:github.com "email blacklist" filetype:txt
```

## 🚀 Performance-Tipps

### Große Listen (>50.000 Einträge):
- Können den Start verlangsamen (5-10 Sekunden)
- Werden gecacht (nur beim ersten Mal oder bei Updates)
- In-Memory Lookup ist sehr schnell (Set-basiert)

### Zu viele Listen:
- Mehr als 10 Quellen können Download-Zeit erhöhen
- Rate-Limiting durch Provider möglich
- Cache hilft bei wiederholten Starts

## 🔐 Sicherheit

### Vertrauenswürdige Quellen verwenden:
- ✅ Spamhaus, Abuse.ch, Blocklist.de
- ✅ Bekannte GitHub-Projekte mit vielen Stars
- ❌ Unbekannte Quellen ohne Dokumentation
- ❌ Listen ohne HTTPS (können manipuliert werden)

### Regelmäßig prüfen:
```bash
# Zeige geladene Quellen
python src/list_manager.py

# Prüfe Logs
tail -f ~/spam_filter.log | grep -i "liste"
```

## 📖 Weitere Ressourcen

- **Spamhaus**: https://www.spamhaus.org/
- **Abuse.ch**: https://abuse.ch/
- **Firebog**: https://firebog.net/
- **DNSBL.info**: https://www.dnsbl.info/

## 💡 Best Practices

1. **Starte mit Standard-Listen** (spamhaus_drop, blocklist_de)
2. **Teste neue Listen einzeln** (aktiviere eine nach der anderen)
3. **Überwache False Positives** (Logs prüfen)
4. **Deaktiviere aggressive Listen** bei zu vielen Fehlalarmen
5. **Nutze die Whitelist** für wichtige Absender
