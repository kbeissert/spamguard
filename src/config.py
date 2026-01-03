"""
Konfiguration-Loader für Spam-Filter mit Multi-Account-Support
Accounts werden aus YAML-Datei geladen
"""

import os
from pathlib import Path
from typing import List, Dict, Any

import yaml
from dotenv import load_dotenv

# Lade .env aus Root
load_dotenv()

# Projekt-Root Verzeichnis
PROJECT_ROOT = Path(__file__).parent.parent

# ============================================
# Konstanten & Prompts
# ============================================

SYSTEM_PROMPT = (
    "You are an intelligent Spam Detection System. "
    "Analyze the email content and metadata critically. "
    "Legitimate emails (HAM) can come from unknown senders. "
    "Only mark as SPAM if there are clear indicators like phishing, scams, unsolicited offers, or malicious content. "
    "The current date is {date}."
)

# ============================================
# YAML Account-Loader
# ============================================


def load_accounts_from_yaml(yaml_path_str: str) -> List[Dict[str, Any]]:
    """
    Lädt E-Mail-Accounts aus YAML-Datei.

    Args:
        yaml_path_str: Pfad zur accounts.yaml

    Returns:
        List[Dict]: Liste von Account-Konfigurationen (nur enabled=true)
    """
    yaml_path = Path(yaml_path_str)
    try:
        # Prüfe ob Pfad absolut ist, sonst relativ zum Projekt-Root
        if not yaml_path.is_absolute():
            yaml_path = PROJECT_ROOT / yaml_path

        with yaml_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "accounts" not in data:
            raise ValueError("accounts.yaml muss einen 'accounts' Schlüssel enthalten")

        # Filtere nur enabled Accounts
        enabled_accounts = [
            acc for acc in data["accounts"] if acc.get("enabled", False)
        ]

        if not enabled_accounts:
            raise ValueError(
                "Keine aktiven Accounts in accounts.yaml gefunden (enabled: true)"
            )

        # Validiere Account-Struktur
        for acc in enabled_accounts:
            required_fields = [
                "name",
                "user",
                "password",
                "server",
                "port",
                "spam_folder",
            ]
            missing = [field for field in required_fields if field not in acc]
            if missing:
                raise ValueError(
                    f"Account '{acc.get('name', 'unknown')}' fehlen Felder: {missing}"
                )

        return enabled_accounts

    except FileNotFoundError as e:
        raise FileNotFoundError(f"❌ accounts.yaml nicht gefunden: {yaml_path}") from e
    except yaml.YAMLError as e:
        raise ValueError(f"❌ Fehler beim Parsen von accounts.yaml: {e}") from e


# ============================================
# Lade Konfiguration
# ============================================

# Account-Datei Pfad
ACCOUNTS_FILE = os.getenv("ACCOUNTS_FILE", "accounts.yaml")

# Lade Accounts aus YAML
EMAIL_ACCOUNTS = load_accounts_from_yaml(ACCOUNTS_FILE)

# Ollama-Settings
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
SPAM_MODEL = os.getenv("SPAM_MODEL", "ministral-3:14b")

# Filter-Settings
FILTER_MODE = os.getenv("FILTER_MODE", "count")  # 'count' oder 'days'
LIMIT = int(os.getenv("LIMIT", "5"))  # Anzahl E-Mails (bei FILTER_MODE=count)
DAYS_BACK = int(os.getenv("DAYS_BACK", "7"))  # Tage zurück (bei FILTER_MODE=days)
LOG_PATH = str(Path(os.getenv("LOG_PATH", "~/spam_filter.log")).expanduser())

# ============================================
# Blacklist/Whitelist Settings
# ============================================

# Aktiviere/Deaktiviere Blacklist/Whitelist-System
USE_LISTS = os.getenv("USE_LISTS", "true").lower() == "true"

# Update-Intervall für externe Blacklists (in Stunden)
LIST_UPDATE_INTERVAL = int(os.getenv("LIST_UPDATE_INTERVAL", "24"))

# Pfade für lokale Listen (relativ zum Projekt-Root)
WHITELIST_FILE = os.getenv("WHITELIST_FILE", "data/lists/whitelist.txt")
BLACKLIST_FILE = os.getenv("BLACKLIST_FILE", "data/lists/blacklist.txt")

# Cache-Verzeichnis für externe Listen
LISTS_CACHE_DIR = os.getenv("LISTS_CACHE_DIR", "data/lists")

# Erzwinge Update beim Start (ignoriert Cache, lädt alle Listen neu)
FORCE_LIST_UPDATE = os.getenv("FORCE_LIST_UPDATE", "false").lower() == "true"
