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


def _load_system_prompt() -> str:
    prompt_file = PROJECT_ROOT / "config" / "system_prompt.txt"
    try:
        return prompt_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(
            f"config/system_prompt.txt nicht gefunden: {prompt_file}\n"
            "Diese Datei sollte im Repository enthalten sein."
        )


SYSTEM_PROMPT = _load_system_prompt()

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
ACCOUNTS_FILE = os.getenv("ACCOUNTS_FILE", "config/accounts.yaml")

# Lade Accounts aus YAML
EMAIL_ACCOUNTS = load_accounts_from_yaml(ACCOUNTS_FILE)

# ============================================
# Filter Settings
# ============================================


def _load_settings() -> dict:
    """Lädt alle Einstellungen aus config/settings.yaml"""
    settings_file = PROJECT_ROOT / "config" / "settings.yaml"
    try:
        with settings_file.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        raise FileNotFoundError(
            f"config/settings.yaml nicht gefunden: {settings_file}\n"
            "Erstelle die Datei: cp config/settings.yaml.example config/settings.yaml"
        )
    except yaml.YAMLError as e:
        raise ValueError(f"Fehler beim Parsen von settings.yaml: {e}") from e


SETTINGS = _load_settings()

_filter = SETTINGS.get("filter", {})
FILTER_MODE = _filter.get("mode", "count")
LIMIT = int(_filter.get("limit", 50))
DAYS_BACK = int(_filter.get("days_back", 7))

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

# ============================================
# Bayesian Filter Settings
# ============================================

BAYESIAN_CONFIG = SETTINGS
BAYESIAN_ENABLED = SETTINGS.get("bayesian", {}).get("enabled", False)
BAYESIAN_LLM_FALLBACK = SETTINGS.get("bayesian", {}).get("llm_fallback", False)
BAYESIAN_THRESHOLDS = SETTINGS.get("bayesian", {}).get("thresholds", {
    "hard_ham": 0.3,
    "hard_spam": 0.5
})
BAYESIAN_MODEL_PATH = PROJECT_ROOT / SETTINGS.get("bayesian", {}).get("model_path", "data/models/bayesian_model.pkl")
BAYESIAN_VECTORIZER_PATH = PROJECT_ROOT / SETTINGS.get("bayesian", {}).get("vectorizer_path", "data/models/vectorizer.pkl")

# Newsletter-Config (3-Klassen-Modus)
NEWSLETTER_CONFIG = SETTINGS.get("bayesian", {}).get("newsletter", {})
NEWSLETTER_ROUTING = NEWSLETTER_CONFIG.get("routing", "ham")
NEWSLETTER_FOLDER = NEWSLETTER_CONFIG.get("folder", "Newsletter")

# Erzwinge Listen-Update beim Start (ignoriert Cache)
FORCE_LIST_UPDATE = os.getenv("FORCE_LIST_UPDATE", "false").lower() == "true"
