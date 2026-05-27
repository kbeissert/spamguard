# Externe Blacklist-Quellen für Spam Guard

## Übersicht

Diese Datei dokumentiert verfügbare externe Blacklist-Quellen und erklärt, wie du eigene Quellen hinzufügen kannst.

## 🔧 Eigene Quellen hinzufügen

### Schritt 1: `config/blacklists.yaml` öffnen

Öffne die Konfigurationsdatei (erstelle sie aus dem Template falls nötig):

```bash
cp config/blacklists.yaml.example config/blacklists.yaml
nano config/blacklists.yaml
```

### Schritt 2: Quelle hinzufügen oder aktivieren

Füge einen neuen Eintrag im YAML-Format hinzu oder setze `enabled: true`:

```yaml
meine_liste:
  url: "https://example.com/spam-list.txt"
  type: "domain"  # ip, ip_cidr, domain oder email
  description: "Beschreibung deiner Liste"
  enabled: true
```

### Schritt 3: Listen herunterladen

```bash
make load-blacklists
```

Beim nächsten `make start` werden alle aktivierten Listen automatisch verwendet.

## 📋 Unterstützte Typen

| Typ | Beschreibung | Beispiel |
|-----|--------------|----------|
| `ip` | Einzelne IP-Adressen | `192.168.1.1` |
| `ip_cidr` | IP-Bereiche (CIDR) | `192.168.1.0/24` |
| `domain` | Domain-Namen | `spam-domain.com` |
| `email` | E-Mail-Adressen | `spam@example.com` |

**Hinweis:** `ip_cidr`-Listen werden korrekt als Netzwerke ausgewertet — eine IP wie `1.2.3.100` wird in `1.2.3.0/24` erkannt.

## 🌐 Verfügbare Blacklist‑Quellen

### IP‑Blacklists (Standard aktiv)

#### Spamhaus DROP
- **URL**: https://www.spamhaus.org/drop/drop.txt
- **Typ**: `ip_cidr`
- **Beschreibung**: Don't Route Or Peer — bekannte Spam‑Netzwerke
- **Update**: Täglich
- **Größe**: ~1.000 Einträge

#### Spamhaus EDROP
- **URL**: https://www.spamhaus.org/drop/edrop.txt
- **Typ**: `ip_cidr`
- **Beschreibung**: Extended DROP — zusätzliche Spam‑Netzwerke
- **Größe**: ~500 Einträge

#### Blocklist.de
- **URL**: https://lists.blocklist.de/lists/all.txt
- **Typ**: `ip`
- **Beschreibung**: IPs mit bekannten Angriffen (SSH, Mail, FTP etc.)
- **Update**: Stündlich
- **Größe**: ~50.000+ Einträge

#### Feodo Tracker
- **URL**: https://feodotracker.abuse.ch/downloads/ipblocklist.txt
- **Typ**: `ip`
- **Beschreibung**: Banking‑Trojaner C2‑Server IPs
- **Größe**: ~500 Einträge

### Domain‑Blacklists (Phishing & Malware)

#### Phishing Army
- **URL**: https://phishing.army/download/phishing_army_blocklist_extended.txt
- **Typ**: `domain`
- **Beschreibung**: Aktuelle Phishing‑Domains
- **Größe**: ~100.000+ Einträge

#### CERT Poland
- **URL**: https://hole.cert.pl/domains/v2/domains.txt
- **Typ**: `domain`
- **Beschreibung**: Phishing‑Domains aus Polen
- **Größe**: ~10.000 Einträge

#### Firebog Malicious
- **URL**: https://v.firebog.net/hosts/Prigent-Malware.txt
- **Typ**: `domain`
- **Beschreibung**: Malware/Phishing‑Domains
- **Größe**: ~15.000 Einträge

#### Abuse.ch URLhaus
- **URL**: https://urlhaus.abuse.ch/downloads/text/
- **Typ**: `domain`
- **Beschreibung**: Aktive Malware‑URLs
- **Größe**: ~10.000+ Einträge

### Spam‑Quellen (optional)

#### StopForumSpam
- **URL**: https://www.stopforumspam.com/downloads/toxic_domains_whole.txt
- **Typ**: `domain`
- **Beschreibung**: Domains bekannter Spam‑Quellen
- **Größe**: ~5.000 Einträge

#### Disposable Email Domains
- **URL**: https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/master/disposable_email_blocklist.conf
- **Typ**: `domain`
- **Beschreibung**: Wegwerf‑E‑Mail‑Provider (z.B. 10minutemail.com)
- **Größe**: ~20.000+ Einträge
- **⚠️ Warnung**: Blockiert ggf. legitime temporäre E‑Mail‑Dienste

### Werbe‑Domains (sehr aggressiv, deaktiviert)

#### Firebog Advertisers
- **URL**: https://v.firebog.net/hosts/Easylist.txt
- **Typ**: `domain`
- **⚠️ Warnung**: Sehr aggressiv — kann auch Newsletter von legitimen Absendern blockieren

## 🎯 Empfohlene Konfigurationen

### Standard (voreingestellt)
Gute Balance aus Schutz und Zuverlässigkeit:
```yaml
spamhaus_drop:    enabled: true   # CIDR-Netzwerke
spamhaus_edrop:   enabled: true   # CIDR-Netzwerke
blocklist_de:     enabled: true   # Einzelne IPs
feodo_tracker:    enabled: true   # C2-Server IPs
phishing_army:    enabled: true   # Phishing-Domains
cert_pl:          enabled: true   # Phishing-Domains
firebog_malicious: enabled: true  # Malware-Domains
abuse_ch_urlhaus:  enabled: true  # Malware-URLs
stopforumspam:    enabled: true   # Spam-Domains
```

### Maximal
Alle Listen aktivieren — kann False Positives verursachen:
```bash
# Setze alle enabled: true in config/blacklists.yaml
make load-blacklists
```
**⚠️ Warnung**: Kann legitime E-Mails blockieren, z.B. Werbe-Domains.

## 🔍 Eigene Quellen finden

### Kriterien für gute Blacklists:
1. ✅ Regelmäßig aktualisiert (täglich/wöchentlich)
2. ✅ Öffentlich zugänglich (HTTP/HTTPS)
3. ✅ Klares Format (eine Zeile pro Eintrag, Kommentare mit `#`)
4. ✅ Dokumentiert und vertrauenswürdig
5. ✅ Keine Authentifizierung erforderlich

## 🚀 Performance-Tipps

### Große Listen (>50.000 Einträge):
- Werden gecacht in `data/lists/external/` (nur beim ersten Mal oder nach `make load-blacklists`)
- In-Memory-Lookup ist sehr schnell (Set-basiert, O(1))
- CIDR-Suche ist linear über die Anzahl der Netzwerke (~1.500 Netze = vernachlässigbar)

### Cache-Verwaltung:
```bash
# Listen manuell aktualisieren
make load-blacklists

# Cache löschen (nächster Filterstart lädt neu)
rm data/lists/external/*.txt
```

## 🔐 Sicherheit

### Vertrauenswürdige Quellen verwenden:
- ✅ Spamhaus, Abuse.ch, Blocklist.de, CERT Poland
- ✅ Bekannte GitHub-Projekte mit vielen Stars
- ❌ Unbekannte Quellen ohne Dokumentation
- ❌ Listen ohne HTTPS (können manipuliert werden)

## 📖 Weitere Ressourcen

- **Spamhaus**: https://www.spamhaus.org/
- **Abuse.ch**: https://abuse.ch/
- **Firebog**: https://firebog.net/
- **DNSBL.info**: https://www.dnsbl.info/

## 💡 Best Practices

1. **Starte mit Standard-Listen** (in `config/blacklists.yaml.example` voreingestellt)
2. **Teste neue Listen einzeln** (aktiviere eine nach der anderen)
3. **Überwache False Positives** (Logs prüfen, Spam-Ordner kontrollieren)
4. **Deaktiviere aggressive Listen** bei zu vielen Fehlalarmen
5. **Nutze die Whitelist** für wichtige Absender (`make unspam adresse@firma.de`)
