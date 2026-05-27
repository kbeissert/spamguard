"""
Ollama Client - Konfiguration und Zugriff auf das lokale LLM.

Alle HTTP-Zugriffe auf Ollama laufen über dieses Modul.
Konfiguration in: config/settings.yaml (Abschnitt "llm:")
"""

import logging
from pathlib import Path
from typing import Tuple

import requests
import yaml

from constants import LLM_MIN_RESPONSE_LENGTH, SPAM_VERDICT_LABELS, HTTP_STATUS_OK

# ============================================
# Konfiguration laden
# ============================================

_CONFIG_FILE = Path(__file__).parent.parent / "config" / "settings.yaml"


def _load_config() -> dict:
    try:
        with _CONFIG_FILE.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return data.get("llm", {})
    except FileNotFoundError:
        raise FileNotFoundError(
            f"config/settings.yaml nicht gefunden: {_CONFIG_FILE}\n"
            "Erstelle die Datei: cp config/settings.yaml.example config/settings.yaml"
        )
    except yaml.YAMLError as e:
        raise ValueError(f"Fehler beim Parsen von settings.yaml: {e}") from e


_cfg = _load_config()

# ============================================
# Öffentliche Konfigurationswerte
# ============================================

ENABLED: bool = _cfg.get("enabled", False)  # Default: LLM-freier Modus
BASE_URL: str = _cfg.get("url", "http://localhost:11434").rstrip("/")
MODEL: str = _cfg.get("model", "")
GENERATE_URL: str = f"{BASE_URL}/api/generate"
CHAT_URL: str = f"{BASE_URL}/api/chat"
TAGS_URL: str = f"{BASE_URL}/api/tags"

_timeouts = _cfg.get("timeouts", {})
INFERENCE_TIMEOUT: int = _timeouts.get("inference", 120)
WARMUP_TIMEOUT: int = _timeouts.get("warmup", 60)
CHECK_TIMEOUT: int = _timeouts.get("availability", 3)

_inference = _cfg.get("inference", {})
TEMPERATURE: float = _inference.get("temperature", 0.1)
NUM_PREDICT: int = _inference.get("num_predict", 150)


# ============================================
# Öffentliche Funktionen
# ============================================


def check_availability() -> bool:
    """
    Prüft ob Ollama erreichbar ist, das konfigurierte Modell vorhanden ist
    und führt einen Warm-up-Request durch.

    Returns:
        True wenn Ollama und Modell einsatzbereit, sonst False
    """
    print("🔍 Prüfe Ollama-Verfügbarkeit...")
    try:
        response = requests.get(TAGS_URL, timeout=CHECK_TIMEOUT)
        if response.status_code != HTTP_STATUS_OK:
            print("⚠️  Ollama antwortet nicht wie erwartet\n")
            return False

        print("✅ Ollama läuft")

        # Prüfe ob Modell verfügbar ist
        print(f"🔍 Prüfe LLM-Modell '{MODEL}'...")
        models_data = response.json()
        available_models = [m["name"] for m in models_data.get("models", [])]

        if MODEL not in available_models:
            print(f"⚠️  Modell '{MODEL}' nicht gefunden!")
            print(
                f"   Verfügbare Modelle: {', '.join(available_models) if available_models else 'keine'}"
            )
            print(f"   Installation: ollama pull {MODEL}")
            print("\n⏹️  Script wird abgebrochen.\n")
            logging.error(f"LLM-Modell {MODEL} nicht verfügbar - Script abgebrochen")
            return False

        print(f"✅ Modell '{MODEL}' ist verfügbar")

        # Warm-up Request
        print(f"🚀 Starte LLM '{MODEL}'...")
        print(
            "   ⏳ Bitte warten, Modell wird geladen (beim ersten Aufruf kann das etwas dauern)..."
        )
        try:
            warmup_response = requests.post(
                GENERATE_URL,
                json={
                    "model": MODEL,
                    "prompt": "Test",
                    "stream": False,
                    "options": {"num_predict": 1},
                },
                timeout=WARMUP_TIMEOUT,
            )
            warmup_response.raise_for_status()
            print(f"✅ LLM '{MODEL}' ist einsatzbereit!\n")
            logging.info(f"LLM {MODEL} erfolgreich initialisiert")
            return True

        except requests.Timeout:
            print("⚠️  LLM-Initialisierung dauert zu lange (Timeout)")
            print(
                "   Das Script läuft weiter, aber LLM-Anfragen könnten langsam sein.\n"
            )
            logging.warning("LLM Warmup Timeout")
            return True
        except Exception as e:
            print(f"⚠️  LLM-Test fehlgeschlagen: {e}")
            print("   Das Script läuft weiter, aber es könnte zu Problemen kommen.\n")
            logging.warning(f"LLM Warmup fehlgeschlagen: {e}")
            return True

    except requests.ConnectionError:
        print("❌ Ollama nicht erreichbar!")
        print("   Starte in anderem Terminal: ollama serve")
        print("   (Oder als Dienst: brew services start ollama)")
        print("   Details: docs/SETUP.md → Abschnitt 'Ollama einrichten'")
        print("\n⏹️  Script wird abgebrochen - keine E-Mails verarbeitet.\n")
        logging.error("Ollama nicht erreichbar - Script abgebrochen")
        return False


def _parse_spam_verdict(result_text: str) -> bool:
    """
    Parse LLM response for a spam verdict.

    Reads the first non-empty line's first word. If it matches a known spam
    category (SPAM/PHISHING/COMMERCIAL), returns True. If HAM, returns False.
    Falls back to scanning all lines, then defaults to HAM (fail-safe).
    """
    if not result_text or len(result_text.strip()) < LLM_MIN_RESPONSE_LENGTH:
        logging.warning("LLM-Antwort zu kurz oder leer, behandle als HAM")
        return False

    lines = result_text.strip().splitlines()

    # Pass 1: first non-empty line's first word
    for line in lines:
        words = line.strip().upper().split()
        if not words:
            continue
        verdict = words[0]
        if verdict in SPAM_VERDICT_LABELS:
            return True
        if verdict == "HAM":
            return False
        break  # first non-empty line didn't yield a known verdict

    # Pass 2: scan all lines for a line starting with a verdict word
    for line in lines:
        words = line.strip().upper().split()
        if not words:
            continue
        if words[0] in SPAM_VERDICT_LABELS:
            return True
        if words[0] == "HAM":
            return False

    logging.warning(f"Uneindeutige LLM-Antwort, behandle als HAM: {result_text[:100]!r}")
    return False


def query_spam(prompt: str, system_prompt: str = "") -> Tuple[bool, str]:
    """
    Sendet einen Spam-Erkennungs-Prompt an Ollama und wertet die Antwort aus.

    Args:
        prompt: Formatierter User-Prompt für die Spam-Erkennung
        system_prompt: System-Prompt mit Kontext und Beispielen für das LLM

    Returns:
        Tuple[bool, str]: (is_spam, reason)
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": TEMPERATURE, "num_predict": NUM_PREDICT},
        "think": False,
    }

    try:
        response = requests.post(CHAT_URL, json=payload, timeout=INFERENCE_TIMEOUT)
        response.raise_for_status()

        result_json = response.json()
        result_text = result_json.get("message", {}).get("content", "").strip()

        is_spam = _parse_spam_verdict(result_text)
        clean_reason = result_text.replace("\n", " ").strip()

        return is_spam, clean_reason

    except requests.Timeout:
        logging.warning("LLM-Request timeout, behandle als HAM")
        return False, "LLM Timeout (als HAM behandelt)"
    except requests.ConnectionError:
        logging.error("Ollama nicht erreichbar - ist 'ollama serve' aktiv?")
        print("\n⚠️  Ollama nicht erreichbar!")
        print("   Starte in anderem Terminal: ollama serve")
        return False, "Ollama offline (als HAM behandelt)"
    except Exception as e:
        logging.error(f"LLM-Fehler: {e}", exc_info=True)
        return False, f"Fehler: {e!s}"
