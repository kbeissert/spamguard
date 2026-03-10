#!/usr/bin/env python3
"""
Blacklist/Whitelist Manager für Ollama Spam Guard
Lädt und verwaltet Spam-Blacklists und Whitelists aus externen Quellen

Update-Intervall: Standardmäßig alle 24 Stunden
Priorität: Whitelist > Blacklist > LLM-Analyse

Autor: Erweitert für Spam-Guard
Datum: 2025-11-20
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Set, List, Tuple, Optional, Dict

import requests
import yaml

from config import PROJECT_ROOT
from constants import (
    EXTERNAL_LIST_DOWNLOAD_TIMEOUT,
    EXTERNAL_LIST_UPDATE_INTERVAL_HOURS,
    MAX_LIST_ENTRY_LENGTH,
)

# ============================================
# Konfiguration
# ============================================

# Verzeichnisse
LISTS_DIR = PROJECT_ROOT / "data" / "lists"  # User White-/Blacklists
CACHE_DIR = PROJECT_ROOT / "data" / "lists" / "external"  # Externe Listen Cache

# Pfad zur Blacklist-Provider Konfiguration
BLACKLIST_SOURCES_FILE = LISTS_DIR / "blacklist_sources.yaml"
BLACKLIST_SOURCES_EXAMPLE = LISTS_DIR / "blacklist_sources.yaml.example"


def _validate_source_config(source_name: str, config: Dict) -> bool:
    """Validiert eine einzelne Blacklist-Quellen-Konfiguration."""
    if not isinstance(config, dict):
        print(f"⚠️  Überspringe '{source_name}': Ungültiges Format (kein Dictionary)")
        logging.warning(
            f"Überspringe Quelle '{source_name}': Erwartet dict, gefunden {type(config).__name__}"
        )
        return False

    required_fields = ["url", "type", "description"]
    missing_fields = [field for field in required_fields if field not in config]

    if missing_fields:
        print(
            f"⚠️  Überspringe '{source_name}': Fehlende Felder: {', '.join(missing_fields)}"
        )
        logging.warning(
            f"Überspringe Quelle '{source_name}': Fehlende Felder: {missing_fields}"
        )
        return False

    url = config.get("url", "")
    if not isinstance(url, str) or not (
        url.startswith("http://") or url.startswith("https://")
    ):
        print(
            f"⚠️  Überspringe '{source_name}': URL muss mit http:// oder https:// beginnen"
        )
        logging.warning(f"Überspringe Quelle '{source_name}': Ungültige URL '{url}'")
        return False

    list_type = config.get("type", "")
    valid_types = ["ip", "ip_cidr", "domain", "email"]
    if list_type not in valid_types:
        print(
            f"⚠️  Überspringe '{source_name}': Ungültiger Typ '{list_type}' (erlaubt: {', '.join(valid_types)})"
        )
        logging.warning(
            f"Überspringe Quelle '{source_name}': Ungültiger Typ '{list_type}'"
        )
        return False

    return True


def _ensure_config_file() -> bool:
    """Stellt sicher, dass die Konfigurationsdatei existiert."""
    if BLACKLIST_SOURCES_FILE.exists():
        return True

    if BLACKLIST_SOURCES_EXAMPLE.exists():
        logging.info(f"Erstelle {BLACKLIST_SOURCES_FILE.name} aus Example-Template")
        print(f"ℹ️  Erstelle {BLACKLIST_SOURCES_FILE.name} aus Template...")
        BLACKLIST_SOURCES_FILE.write_text(
            BLACKLIST_SOURCES_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8"
        )
        return True

    error_msg = (
        f"❌ FEHLER: Keine Blacklist-Quellen Konfiguration gefunden!\n"
        f"   Erwartet: {BLACKLIST_SOURCES_FILE}\n"
        f"   Template: {BLACKLIST_SOURCES_EXAMPLE}\n"
        f"   Bitte erstelle die Datei aus dem Template."
    )
    logging.error(error_msg)
    print(error_msg)
    return False


def _load_yaml_content() -> Optional[Dict]:
    """Lädt den Inhalt der YAML-Datei."""
    try:
        with BLACKLIST_SOURCES_FILE.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else None
    except yaml.YAMLError as e:
        error_msg = (
            f"❌ YAML SYNTAX-FEHLER in {BLACKLIST_SOURCES_FILE.name}:\n"
            f"   {str(e)}\n\n"
            f"   Häufige Fehler:\n"
            f"   - Falsche Einrückung (nutze 2 Leerzeichen, keine Tabs)\n"
            f"   - Fehlende Anführungszeichen bei URLs\n"
            f"   - Doppelpunkt vergessen nach Quelle-Name\n\n"
            f"   Validiere die Syntax z.B. mit: yamllint {BLACKLIST_SOURCES_FILE}\n"
            f"   Oder online: https://www.yamllint.com/\n\n"
            f"   ℹ️  Externe Blacklists werden NICHT geladen!"
        )
        logging.error(f"YAML Syntax-Fehler in {BLACKLIST_SOURCES_FILE.name}: {e}")
        print(error_msg)
        return None
    except Exception as e:
        error_msg = (
            f"❌ FEHLER beim Laden von {BLACKLIST_SOURCES_FILE.name}:\n"
            f"   {str(e)}\n"
            f"   Prüfe die Datei auf Fehler!"
        )
        logging.error(
            f"Fehler beim Laden von {BLACKLIST_SOURCES_FILE.name}: {e}", exc_info=True
        )
        print(error_msg)
        return None


# Lade Blacklist-Quellen aus YAML
def load_blacklist_sources() -> Dict[str, dict]:
    """
    Lädt externe Blacklist-Quellen aus YAML-Datei.
    Falls Datei nicht existiert, wird sie aus Example erstellt.
    Validiert alle Einträge und gibt detaillierte Fehlermeldungen aus.

    Returns:
        Dict mit validierten Blacklist-Quellen
    """
    if not _ensure_config_file():
        return {}

    sources = _load_yaml_content()

    # Prüfe ob YAML leer ist
    if sources is None:
        # Fehler wurde bereits in _load_yaml_content geloggt
        if BLACKLIST_SOURCES_FILE.exists() and BLACKLIST_SOURCES_FILE.stat().st_size == 0:
            logging.warning(
                f"{BLACKLIST_SOURCES_FILE.name} ist leer, keine externen Blacklists konfiguriert"
            )
        return {}

    if not isinstance(sources, dict):
        error_msg = (
            f"❌ FEHLER in {BLACKLIST_SOURCES_FILE.name}:\n"
            f"   Ungültiges Format! Erwartet: YAML Dictionary\n"
            f"   Gefunden: {type(sources).__name__}\n"
            f"   Prüfe die YAML-Syntax!"
        )
        logging.error(error_msg)
        print(error_msg)
        return {}

    # Validiere jeden Eintrag
    valid_sources = {}
    invalid_count = 0

    for source_name, config in sources.items():
        if not _validate_source_config(source_name, config):
            invalid_count += 1
            continue

        # Validiere enabled Flag (optional, default: True)
        enabled = config.get("enabled", True)
        if not isinstance(enabled, bool):
            print(
                f"⚠️  '{source_name}': 'enabled' muss true/false sein, nicht '{enabled}' - setze auf false"
            )
            logging.warning(
                f"Quelle '{source_name}': Ungültiger enabled-Wert '{enabled}', setze auf false"
            )
            config["enabled"] = False

        # Alles OK, füge hinzu
        valid_sources[source_name] = config

    # Zusammenfassung
    if invalid_count > 0:
        print(
            f"⚠️  {invalid_count} ungültige Einträge in {BLACKLIST_SOURCES_FILE.name} übersprungen"
        )
        logging.warning(
            f"{invalid_count} ungültige Einträge in {BLACKLIST_SOURCES_FILE.name} übersprungen"
        )

    if valid_sources:
        logging.info(
            f"Blacklist-Quellen geladen: {len(valid_sources)} gültige Einträge aus {BLACKLIST_SOURCES_FILE.name}"
        )
    else:
        print(
            f"⚠️  Keine gültigen Blacklist-Quellen in {BLACKLIST_SOURCES_FILE.name} gefunden!"
        )
        logging.warning(
            f"Keine gültigen Blacklist-Quellen in {BLACKLIST_SOURCES_FILE.name}"
        )

    return valid_sources


# Lade Quellen beim Import
BLACKLIST_SOURCES = load_blacklist_sources()

# Lokale Listen-Pfade (relativ zum Projekt-Root)
# Diese liegen direkt in data/lists/ (getrennt vom Cache)
LOCAL_WHITELIST_PATH = "data/lists/whitelist.txt"
LOCAL_BLACKLIST_PATH = "data/lists/blacklist.txt"

# Externe Listen werden in data/lists/external/ gecacht

# ============================================
# List Manager Klasse
# ============================================


@dataclass
class _ListData:
    """Groups the three sets that make up one list (email, domain, IP)."""

    emails: Set[str] = field(default_factory=set)
    domains: Set[str] = field(default_factory=set)
    ips: Set[str] = field(default_factory=set)


class ListManager:
    """
    Verwaltet Spam-Blacklists und Whitelists.

    Funktionen:
    - Lädt lokale White-/Blacklists aus Textdateien
    - Lädt externe Blacklists von öffentlichen Quellen
    - Cached Listen mit konfigurierbarem Update-Intervall
    - Prüft E-Mail-Adressen, Domains und IPs gegen Listen
    - Priorität: Whitelist > Blacklist
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        update_interval_hours: int = EXTERNAL_LIST_UPDATE_INTERVAL_HOURS,
    ):
        """
        Initialisiert den ListManager.

        Args:
            cache_dir: Verzeichnis für gecachte externe Listen (Standard: CACHE_DIR = data/lists/external/)
            update_interval_hours: Update-Intervall in Stunden (Standard: 24)
        """
        self.cache_dir = cache_dir or CACHE_DIR
        self.update_interval = timedelta(hours=update_interval_hours)

        # Erstelle beide Verzeichnisse falls nicht vorhanden
        LISTS_DIR.mkdir(parents=True, exist_ok=True)  # Für User White-/Blacklists
        self.cache_dir.mkdir(parents=True, exist_ok=True)  # Für externe Listen Cache

        # Listen als Sets für schnelle Lookup-Performance
        self.whitelist = _ListData()
        self.blacklist = _ListData()

        # Metadaten für Updates
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata = self._load_metadata()

        logging.info(f"ListManager initialisiert. Cache-Dir: {self.cache_dir}")

    # ============================================
    # Laden und Aktualisieren
    # ============================================

    def load_all_lists(self, force_update: bool = False) -> None:
        """
        Lädt alle Listen (lokal + extern).

        Args:
            force_update: Erzwingt Update auch wenn Cache gültig ist
        """
        logging.info("Lade alle Listen...")

        # Lokale Listen laden
        self._load_local_whitelist()
        self._load_local_blacklist()

        # Externe Blacklists laden/aktualisieren
        self._load_external_blacklists(force_update=force_update)

        logging.info(
            f"Listen geladen: "
            f"Whitelist ({len(self.whitelist.emails)} E-Mails, {len(self.whitelist.domains)} Domains), "
            f"Blacklist ({len(self.blacklist.emails)} E-Mails, {len(self.blacklist.domains)} Domains, "
            f"{len(self.blacklist.ips)} IPs)"
        )

    def _validate_and_add_entry(
        self,
        entry: str,
        list_name: str,
        line_num: int,
        target_emails: Set[str],
        target_domains: Set[str],
    ) -> bool:
        """Validiert einen Eintrag und fügt ihn der entsprechenden Liste hinzu."""
        if not entry or len(entry) > MAX_LIST_ENTRY_LENGTH:
            print(
                f"⚠️  {list_name} Zeile {line_num}: Ungültiger Eintrag (zu lang oder leer)"
            )
            logging.warning(
                f"{list_name} Zeile {line_num}: Ungültiger Eintrag übersprungen"
            )
            return False

        # Domain-Logik (startet mit @ oder enthält kein @)
        if entry.startswith("@") or "@" not in entry:
            domain = entry[1:].strip() if entry.startswith("@") else entry

            if not domain or " " in domain:
                print(
                    f"⚠️  {list_name} Zeile {line_num}: Domain darf keine Leerzeichen enthalten: {entry}"
                )
                logging.warning(
                    f"{list_name} Zeile {line_num}: Ungültige Domain: {entry}"
                )
                return False

            target_domains.add(domain.lower())
            return True

        # E-Mail-Logik
        if entry.count("@") != 1:
            print(
                f"⚠️  {list_name} Zeile {line_num}: Ungültige E-Mail (mehrere @): {entry}"
            )
            logging.warning(
                f"{list_name} Zeile {line_num}: Ungültige E-Mail: {entry}"
            )
            return False

        target_emails.add(entry.lower())
        return True

    def _load_generic_list(
        self,
        file_path: Path,
        list_name: str,
        target_emails: Set[str],
        target_domains: Set[str],
        default_content: str,
    ) -> None:
        """
        Generische Funktion zum Laden lokaler Listen.

        Args:
            file_path: Pfad zur Datei
            list_name: Name der Liste für Logs (z.B. "Whitelist")
            target_emails: Set für E-Mails
            target_domains: Set für Domains
            default_content: Inhalt für neue Datei falls nicht existent
        """
        if not file_path.exists():
            logging.warning(f"Lokale {list_name} nicht gefunden: {file_path}")
            print(f"ℹ️  Erstelle leere {list_name}: {file_path}")
            logging.info(f"Erstelle leere {list_name}-Datei...")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(default_content, encoding="utf-8")
            return

        try:
            entries = self._parse_list_file(file_path)
            invalid_count = 0

            for line_num, entry in enumerate(entries, start=1):
                if not self._validate_and_add_entry(
                    entry, list_name, line_num, target_emails, target_domains
                ):
                    invalid_count += 1

            valid_count = len(entries) - invalid_count
            if invalid_count > 0:
                print(f"⚠️  {list_name}: {invalid_count} ungültige Einträge übersprungen")

            logging.info(
                f"{list_name} geladen: {valid_count} gültige von {len(entries)} Einträgen aus {file_path}"
            )

        except Exception as e:
            error_msg = (
                f"❌ FEHLER beim Laden der {list_name} ({file_path}):\n"
                f"   {str(e)}\n"
                f"   Prüfe die Datei auf Fehler!"
            )
            print(error_msg)
            logging.error(f"Fehler beim Laden der {list_name}: {e}", exc_info=True)

    def _load_local_whitelist(self) -> None:
        """Lädt lokale Whitelist aus Textdatei (data/lists/whitelist.txt)."""
        whitelist_path = LISTS_DIR / "whitelist.txt"
        default_content = (
            "# Whitelist - Eine E-Mail oder Domain pro Zeile\n"
            "# Beispiel:\n# trusted@example.com\n# example.com\n"
        )
        self._load_generic_list(
            whitelist_path,
            "Whitelist",
            self.whitelist.emails,
            self.whitelist.domains,
            default_content,
        )

    def _load_local_blacklist(self) -> None:
        """Lädt lokale Blacklist aus Textdatei (data/lists/blacklist.txt)."""
        blacklist_path = LISTS_DIR / "blacklist.txt"
        default_content = (
            "# Blacklist - Eine E-Mail oder Domain pro Zeile\n"
            "# Beispiel:\n# spam@example.com\n# spammer-domain.com\n"
        )
        self._load_generic_list(
            blacklist_path,
            "Blacklist",
            self.blacklist.emails,
            self.blacklist.domains,
            default_content,
        )

    def _load_external_blacklists(self, force_update: bool = False) -> None:
        """
        Lädt externe Blacklists von konfigurierten Quellen.

        Args:
            force_update: Erzwingt Download auch wenn Cache gültig ist
        """
        # Filtere nur aktivierte Quellen
        enabled_sources = {
            name: config
            for name, config in BLACKLIST_SOURCES.items()
            if config.get(
                "enabled", True
            )  # Default: enabled=True falls nicht angegeben
        }

        if not enabled_sources:
            logging.info("Keine externen Blacklist-Quellen aktiviert")
            return

        print(
            f"   🌐 Prüfe externe Blacklists ({len(enabled_sources)} Quellen aktiviert, {len(BLACKLIST_SOURCES) - len(enabled_sources)} deaktiviert)..."
        )

        for source_name, source_config in enabled_sources.items():
            cache_file = self.cache_dir / f"{source_name}.txt"

            # Prüfe ob Update nötig ist
            if not force_update and self._is_cache_valid(source_name):
                cache_age = self._get_cache_age(source_name)
                print(
                    f"      ✅ {source_config['description']}: Cache gültig (vor {cache_age} aktualisiert)"
                )
                logging.info(f"Cache für {source_name} ist aktuell, lade aus Cache...")
                self._load_from_cache(cache_file, source_config["type"])
                continue

            # Download externe Liste
            try:
                print(
                    f"      ⏳ {source_config['description']}: Lade von {source_config['url']}..."
                )
                logging.info(f"Lade externe Liste: {source_config['description']}")
                response = requests.get(source_config["url"], timeout=EXTERNAL_LIST_DOWNLOAD_TIMEOUT)
                response.raise_for_status()

                # Speichere im Cache
                cache_file.write_text(response.text, encoding="utf-8")

                # Parse und füge zu Blacklist hinzu
                entries_count_before = len(self.blacklist.ips) + len(
                    self.blacklist.domains
                )
                self._load_from_cache(cache_file, source_config["type"])
                entries_count_after = len(self.blacklist.ips) + len(
                    self.blacklist.domains
                )
                new_entries = entries_count_after - entries_count_before

                # Update Metadaten
                self.metadata[source_name] = {
                    "last_update": datetime.now().isoformat(),
                    "url": source_config["url"],
                    "type": source_config["type"],
                }
                self._save_metadata()

                print(
                    f"      ✅ {source_config['description']}: {new_entries} Einträge hinzugefügt"
                )
                logging.info(
                    f"Externe Liste {source_name} erfolgreich geladen ({new_entries} neue Einträge)"
                )

            except requests.RequestException as e:
                logging.error(f"Fehler beim Laden von {source_name}: {e}")
                # Versuche aus Cache zu laden falls vorhanden
                if cache_file.exists():
                    print(
                        f"      ⚠️  {source_config['description']}: Download fehlgeschlagen, verwende Cache"
                    )
                    logging.warning(f"Verwende alten Cache für {source_name}")
                    self._load_from_cache(cache_file, source_config["type"])
                else:
                    print(
                        f"      ❌ {source_config['description']}: Download fehlgeschlagen, kein Cache verfügbar"
                    )

    def _load_from_cache(self, cache_file: Path, list_type: str) -> None:
        """
        Lädt Liste aus Cache-Datei.

        Args:
            cache_file: Pfad zur Cache-Datei
            list_type: Typ der Liste (ip, domain, ip_cidr, email)
        """
        if not cache_file.exists():
            return

        entries = self._parse_list_file(cache_file)

        if list_type == "ip":
            self.blacklist.ips.update(entries)
        elif list_type == "domain":
            self.blacklist.domains.update(entry.lower() for entry in entries)
        elif list_type == "email":
            self.blacklist.emails.update(entry.lower() for entry in entries)
        elif list_type == "ip_cidr":
            # Für CIDR-Blöcke extrahieren wir IPs (vereinfacht)
            for entry in entries:
                # Extrahiere IP aus CIDR-Notation (z.B. "192.168.1.0/24")
                if "/" in entry:
                    ip = entry.split("/")[0]
                    self.blacklist.ips.add(ip)
                else:
                    self.blacklist.ips.add(entry)

    def _parse_list_file(self, file_path: Path) -> List[str]:
        """
        Parsed Textdatei und gibt gereinigte Einträge zurück.

        Args:
            file_path: Pfad zur Textdatei

        Returns:
            List[str]: Gereinigte Einträge (ohne Kommentare, Leerzeilen)
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            entries = []

            for raw_line in content.splitlines():
                # Entferne Kommentare und Whitespace
                line = raw_line.split("#")[0].strip()
                if line:
                    entries.append(line)

            return entries

        except Exception as e:
            logging.error(f"Fehler beim Parsen von {file_path}: {e}")
            return []

    # ============================================
    # Prüfungs-Funktionen
    # ============================================

    def check_email(self, email_address: str) -> Tuple[bool, Optional[str]]:
        """
        Prüft E-Mail-Adresse gegen White-/Blacklist.

        Priorität:
        1. Whitelist (E-Mail oder Domain) → kein Spam
        2. Blacklist (E-Mail oder Domain) → Spam
        3. None → unbekannt, LLM-Prüfung nötig

        Args:
            email_address: Zu prüfende E-Mail-Adresse

        Returns:
            Tuple[bool, Optional[str]]: (is_spam, reason)
            - (False, "Whitelist: email") wenn auf Whitelist
            - (True, "Blacklist: domain") wenn auf Blacklist
            - (False, None) wenn nicht in Listen (geändert von None, None für Typsicherheit)
        """
        if not email_address or "@" not in email_address:
            return False, None

        email_lower = email_address.lower().strip()
        domain = email_lower.split("@")[1] if "@" in email_lower else ""

        # 1. Prüfe Whitelist (höchste Priorität)
        if email_lower in self.whitelist.emails:
            logging.info(f"✅ E-Mail auf Whitelist: {email_address}")
            return False, f"Whitelist: {email_address}"

        # Prüfe Domain und alle übergeordneten Domains (Subdomain-Check)
        # Beispiel: mail.google.com -> prüft mail.google.com, google.com, com
        if domain:
            parts = domain.split(".")
            # Wir prüfen von spezifisch nach allgemein, aber stoppen vor der TLD (letzter Teil)
            # Mindestens Domain + TLD müssen übrig bleiben (z.B. google.com)
            for i in range(len(parts) - 1):
                parent_domain = ".".join(parts[i:])
                if parent_domain in self.whitelist.domains:
                    logging.info(f"✅ Domain auf Whitelist: {parent_domain} (Match für {domain})")
                    return False, f"Whitelist: @{parent_domain}"

        # 2. Prüfe Blacklist
        if email_lower in self.blacklist.emails:
            logging.info(f"🚫 E-Mail auf Blacklist: {email_address}")
            return True, f"Blacklist: {email_address}"

        # Prüfe Domain und alle übergeordneten Domains (Subdomain-Check)
        if domain:
            parts = domain.split(".")
            for i in range(len(parts) - 1):
                parent_domain = ".".join(parts[i:])
                if parent_domain in self.blacklist.domains:
                    logging.info(f"🚫 Domain auf Blacklist: {parent_domain} (Match für {domain})")
                    return True, f"Blacklist: @{parent_domain}"

        # 3. Nicht in Listen gefunden
        return False, None

    def check_ip(self, ip_address: str) -> Tuple[bool, Optional[str]]:
        """
        Prüft IP-Adresse gegen Blacklist.

        Args:
            ip_address: Zu prüfende IP-Adresse

        Returns:
            Tuple[bool, Optional[str]]: (is_spam, reason)
        """
        if not ip_address:
            return False, None

        ip_clean = ip_address.strip()

        if ip_clean in self.blacklist.ips:
            logging.info(f"🚫 IP auf Blacklist: {ip_address}")
            return True, f"Blacklist IP: {ip_address}"

        return False, None

    # ============================================
    # Metadata & Caching
    # ============================================

    def _load_metadata(self) -> dict:
        """Lädt Metadaten aus JSON-Datei."""
        if self.metadata_file.exists():
            try:
                data = json.loads(self.metadata_file.read_text(encoding="utf-8"))
                return data if isinstance(data, dict) else {}
            except Exception as e:
                logging.error(f"Fehler beim Laden von Metadaten: {e}")
        return {}

    def _save_metadata(self) -> None:
        """Speichert Metadaten in JSON-Datei."""
        try:
            self.metadata_file.write_text(
                json.dumps(self.metadata, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logging.error(f"Fehler beim Speichern von Metadaten: {e}")

    def _is_cache_valid(self, source_name: str) -> bool:
        """
        Prüft ob Cache für Quelle noch gültig ist.

        Args:
            source_name: Name der Quelle

        Returns:
            bool: True wenn Cache gültig (innerhalb Update-Intervall)
        """
        if source_name not in self.metadata:
            return False

        try:
            last_update = datetime.fromisoformat(
                self.metadata[source_name]["last_update"]
            )
            return datetime.now() - last_update < self.update_interval
        except (KeyError, ValueError, TypeError) as e:
            logging.debug(f"Cache validation failed for {source_name}: {e}")
            return False

    def _get_cache_age(self, source_name: str) -> str:
        """
        Gibt das Alter des Caches als lesbaren String zurück.

        Args:
            source_name: Name der Quelle

        Returns:
            str: Zeitangabe wie "2h 30m" oder "1d 5h"
        """
        if source_name not in self.metadata:
            return "unbekannt"

        try:
            last_update = datetime.fromisoformat(
                self.metadata[source_name]["last_update"]
            )
            age = datetime.now() - last_update

            if age.days > 0:
                hours = age.seconds // 3600
                return f"{age.days}d {hours}h"

            hours = age.seconds // 3600
            minutes = (age.seconds % 3600) // 60
            if hours > 0:
                return f"{hours}h {minutes}m"

            return f"{minutes}m"
        except (KeyError, ValueError, TypeError) as e:
            logging.debug(f"Cache age calculation failed for {source_name}: {e}")
            return "unbekannt"

    # ============================================
    # Statistiken & Info
    # ============================================

    def get_stats(self) -> dict:
        """
        Gibt Statistiken über geladene Listen zurück.

        Returns:
            dict: Statistiken (Anzahl Einträge, letzte Updates etc.)
        """
        return {
            "whitelist": {
                "emails": len(self.whitelist.emails),
                "domains": len(self.whitelist.domains),
                "total": len(self.whitelist.emails) + len(self.whitelist.domains),
            },
            "blacklist": {
                "emails": len(self.blacklist.emails),
                "domains": len(self.blacklist.domains),
                "ips": len(self.blacklist.ips),
                "total": len(self.blacklist.emails)
                + len(self.blacklist.domains)
                + len(self.blacklist.ips),
            },
            "cache": {
                "directory": str(self.cache_dir),
                "sources": list(self.metadata.keys()),
                "last_updates": {
                    name: data.get("last_update", "unknown")
                    for name, data in self.metadata.items()
                },
            },
        }

    def force_update(self) -> None:
        """Erzwingt Update aller externen Listen."""
        logging.info("Erzwinge Update aller externen Listen...")
        self._load_external_blacklists(force_update=True)

    # ============================================
    # Singleton-Instanz
    # ============================================

    _instance: Optional["ListManager"] = None

    @classmethod
    def get_instance(cls) -> "ListManager":
        """
        Gibt Singleton-Instanz des ListManagers zurück.

        Returns:
            ListManager: Singleton-Instanz
        """
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.load_all_lists()
        return cls._instance


def get_list_manager() -> ListManager:
    """
    Wrapper für ListManager.get_instance() für Abwärtskompatibilität.

    Returns:
        ListManager: Singleton-Instanz
    """
    return ListManager.get_instance()


# ============================================
# CLI für Tests
# ============================================

if __name__ == "__main__":
    # Test-Setup
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("🔧 Initialisiere ListManager...")
    manager = get_list_manager()  # pylint: disable=invalid-name

    print("\n📊 Statistiken:")
    stats = manager.get_stats()
    print(f"   Whitelist: {stats['whitelist']['total']} Einträge")
    print(f"   Blacklist: {stats['blacklist']['total']} Einträge")
    print(f"   Cache: {stats['cache']['directory']}")

    print("\n🧪 Test-Prüfungen:")

    # Test E-Mail Checks
    test_emails = ["admin@example.com", "spam@spammer.com", "user@trusted-domain.com"]

    for email in test_emails:
        is_spam, reason = manager.check_email(email)
        if is_spam is None:
            print(f"   {email}: ❓ Unbekannt → LLM-Prüfung")
        elif is_spam:
            print(f"   {email}: 🚫 SPAM ({reason})")
        else:
            print(f"   {email}: ✅ HAM ({reason})")

    print("\n✅ ListManager bereit!")
