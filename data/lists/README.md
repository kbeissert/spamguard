# Whitelist/Blacklist Verzeichnis

## Dateien

```
data/lists/
├── whitelist.txt               # Deine Whitelist (persönlich, nicht in Git)
├── blacklist.txt               # Deine Blacklist (persönlich, nicht in Git)
├── whitelist.txt.example       # Template für Whitelist
├── blacklist.txt.example       # Template für Blacklist
└── external/                   # Cache für externe Listen (nicht in Git)
    ├── spamhaus_drop.txt       # Automatisch geladen
    ├── blocklist_de.txt        # Automatisch geladen
    └── metadata.json           # Update-Zeitstempel
```

## Whitelist / Blacklist

Beide Dateien verwenden einfaches Textformat: eine Adresse oder Domain pro Zeile, `#` für Kommentare.

```
# Beispiel
trusted@example.com
trusted-domain.de
```

## Externe Blacklist-Quellen

Die Konfiguration der externen Quellen liegt in `config/blacklists.yaml` (aus Template `config/blacklists.yaml.example` erstellen).

Quellen herunterladen:
```bash
make load-blacklists
```

Weitere Infos: `docs/BLACKLIST_SOURCES.md`
