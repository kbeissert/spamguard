#!/usr/bin/env python3
"""
Ollama Spam Guard - IMAP Spam Filter mit lokalem LLM (qwen2.5:14b-instruct via Ollama)

3-stufige Spam-Erkennung:
1. Whitelist-Check (höchste Priorität) → kein Spam
2. Blacklist-Check mit externen Spam-Listen → Spam
3. LLM-Analyse via Ollama (nur falls nicht in Listen)

Features:
- Multi-Account Support (IMAP)
- Externe Blacklist-Provider (Spamhaus, Blocklist.de, etc.)
- Whitelist/Blacklist Management mit Validierung
- Spam-Absender-Übersicht nach Filterung
- E-Mail-Wiederherstellung (Unspam-Tool)

Autor: Generiert mit Continue + Codepilot
Datum: 2025-11-20
"""

import email
import email.header
import email.utils
import imaplib
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import requests
from tqdm import tqdm

from config import (
    DAYS_BACK,
    EMAIL_ACCOUNTS,
    FILTER_MODE,
    LIMIT,
    LOG_PATH,
    OLLAMA_URL,
    SPAM_MODEL,
    SYSTEM_PROMPT,
    USE_LISTS,
    LIST_UPDATE_INTERVAL,
    FORCE_LIST_UPDATE,
    LISTS_CACHE_DIR,
    PROJECT_ROOT,
)
from list_manager import ListManager
from utils import decode_header_safe, extract_body_preview

# Constants
MAX_SUBJECT_LENGTH = 60
MAX_SUMMARY_SUBJECT_LENGTH = 70
MAX_SUBJECTS_TO_SHOW = 3
HTTP_OK = 200
LLM_TIMEOUT = 120
LLM_WARMUP_TIMEOUT = 60
OLLAMA_CHECK_TIMEOUT = 3

# Logging-Setup
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ============================================
# Blacklist/Whitelist Manager (global)
# ============================================

def create_list_manager() -> Optional[ListManager]:
    """
    Initialisiert den ListManager.

    Returns:
        ListManager oder None falls deaktiviert
    """
    if not USE_LISTS:
        logging.info("Blacklist/Whitelist-System deaktiviert (USE_LISTS=false)")
        return None

    try:
        # Cache für externe Listen in separatem Unterverzeichnis
        cache_dir = PROJECT_ROOT / LISTS_CACHE_DIR / "external"

        print("🔍 Initialisiere Blacklist/Whitelist-System...")
        logging.info(
            f"Initialisiere Blacklist/Whitelist-System (Update-Intervall: {LIST_UPDATE_INTERVAL}h)"
        )
        logging.info("User-Listen: data/lists/, Cache: data/lists/external/")

        list_manager = ListManager(
            cache_dir=cache_dir, update_interval_hours=LIST_UPDATE_INTERVAL
        )
        list_manager.load_all_lists(force_update=FORCE_LIST_UPDATE)

        # Zeige Statistiken
        stats = list_manager.get_stats()
        print("✅ Listen geladen:")
        print(
            f"   📋 Whitelist: {stats['whitelist']['total']} Einträge ({stats['whitelist']['emails']} E-Mails, {stats['whitelist']['domains']} Domains)"
        )
        print(
            f"   🚫 Blacklist: {stats['blacklist']['total']} Einträge ({stats['blacklist']['emails']} E-Mails, {stats['blacklist']['domains']} Domains, {stats['blacklist']['ips']} IPs)"
        )

        # Zeige Info zu externen Listen
        if stats["cache"]["sources"]:
            print(f"   🌐 Externe Listen: {', '.join(stats['cache']['sources'])}")

        logging.info(
            f"Listen geladen: Whitelist={stats['whitelist']['total']}, "
            f"Blacklist={stats['blacklist']['total']}"
        )

        return list_manager

    except Exception as e:
        logging.error(
            f"Fehler beim Initialisieren des ListManagers: {e}", exc_info=True
        )
        print(f"⚠️  Blacklist/Whitelist-System konnte nicht geladen werden: {e}")
        return None


# ============================================
# IMAP-Funktionen
# ============================================


def connect_imap(account: Dict[str, str]) -> imaplib.IMAP4_SSL:
    """
    Verbindet zum IMAP-Server und öffnet INBOX.

    Args:
        account: Account-Konfiguration (user, password, server, port)

    Returns:
        IMAP4_SSL: Verbundenes Mail-Objekt

    Raises:
        imaplib.IMAP4.error: Bei Login- oder Verbindungsfehlern
    """
    try:
        print(f"🔌 Verbinde zu {account['server']}:{account['port']}...")
        mail = imaplib.IMAP4_SSL(account["server"], int(account["port"]))

        print(f"🔐 Login {account['name']}...")
        mail.login(account["user"], account["password"])

        print("📬 Öffne INBOX...")
        mail.select("INBOX")

        logging.info(
            f"Erfolgreich verbunden mit {account['server']} ({account['name']})"
        )
        return mail

    except imaplib.IMAP4.error as e:
        print(f"\n❌ IMAP-Fehler: {e}")
        print("\n💡 Mögliche Ursachen:")
        print("   - Falsches Passwort")
        print("   - IMAP nicht aktiviert")
        print(f"   - Falscher Server ({account['server']})")
        logging.error(f"IMAP-Fehler für {account['user']}: {e}", exc_info=True)
        raise
    except Exception as e:
        print(f"\n❌ Verbindungsfehler: {e}")
        logging.error(
            f"Verbindungsfehler zu {account['server']}:{account['port']}", exc_info=True
        )
        raise


# ============================================
# Spam-Detection mit LLM
# ============================================


def detect_spam(
    sender: str, subject: str, body: str, list_manager: Optional[ListManager] = None
) -> Tuple[bool, str]:
    """
    Analysiert E-Mail mit 3-stufigem Ansatz:
    1. Whitelist-Check (höchste Priorität) → kein Spam
    2. Blacklist-Check → Spam
    3. LLM-Analyse via qwen2.5:14b-instruct (falls nicht in Listen)

    Args:
        sender: Absender-E-Mail
        subject: E-Mail-Betreff
        body: E-Mail-Body (Preview, max 500 Zeichen)
        list_manager: Optionaler ListManager für Whitelist/Blacklist Checks

    Returns:
        Tuple[bool, str]: (is_spam, reason)
    """
    # ============================================
    # STUFE 1 & 2: Whitelist/Blacklist Check (Hard Filter)
    # ============================================

    if list_manager:
        # Prüfe E-Mail gegen Listen
        is_spam_by_list, list_reason = list_manager.check_email(sender)

        if list_reason is not None:
            # E-Mail wurde in Liste gefunden (Whitelist oder Blacklist)
            logging.info(f"Hard Filter: {sender} → {list_reason}")
            return is_spam_by_list, list_reason

        # E-Mail nicht in Listen → LLM-Analyse durchführen
        logging.debug(
            f"E-Mail nicht in Listen gefunden, führe LLM-Analyse durch: {sender}"
        )

    # ============================================
    # STUFE 3: LLM-basierte Spam-Erkennung
    # ============================================

    # Prompt-Design aus Benchmark übernommen (optimiert für Ministral/Qwen)
    prompt = (
        f"Klassifiziere diese E-Mail als SPAM oder HAM. "
        f"Antworte NUR mit 'SPAM' oder 'HAM' und einer kurzen Begründung (max 15 Wörter).\n\n"
        f"Von: {sender}\n"
        f"Betreff: {subject}\n"
        f"Inhalt: {body[:1000]}"  # Mehr Kontext als vorher (500 -> 1000)
    )

    # Konfiguration analog zum Benchmark
    # Standardmäßig kein "Thinking" für maximale Geschwindigkeit im Produktivbetrieb
    use_thinking = False
    num_predict = 2000 if use_thinking else 150
    timeout = 120  # Erhöht von 30s auf 120s für Stabilität

    payload = {
        "model": SPAM_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": num_predict},
    }

    # Ministral-Optimierung: Lightweight System-Prompt
    # Reduziert Input-Tokens von ~600 auf ~50 und steigert Effizienz
    if "ministral" in SPAM_MODEL.lower():
        payload["system"] = SYSTEM_PROMPT.format(date=datetime.now().strftime('%Y-%m-%d'))

    # Deaktiviere Thinking explizit, falls nicht gewünscht
    if not use_thinking:
        payload["think"] = False

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        response.raise_for_status()

        # Parse Ollama JSON-Response
        result_json = response.json()
        result_text = result_json.get("response", "").strip()

        # Bestimme Spam-Status
        # Suche nach "SPAM" im gesamten Antworttext, da Benchmark-Prompt Begründung enthält
        is_spam = "SPAM" in result_text.upper()

        # Bereinige den Text für das Log (entferne Newlines)
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
        return False, f"Fehler: {str(e)}"


# ============================================
# E-Mail-Verarbeitung
# ============================================









def _process_single_email(
    mail: imaplib.IMAP4_SSL,
    email_id: bytes,
    account: Dict[str, str],
    list_manager: Optional[ListManager],
    stats: Dict[str, Any],
) -> None:
    """Verarbeitet eine einzelne E-Mail."""
    try:
        # ID dekodieren für IMAP-Befehle
        email_id_str = email_id.decode("utf-8")

        # Hole E-Mail
        status, msg_data = mail.fetch(email_id_str, "(RFC822)")
        if status != "OK":
            logging.error(f"Fetch fehlgeschlagen für ID {email_id_str}")
            return

        # Parse E-Mail
        raw_email = msg_data[0]
        if isinstance(raw_email, tuple):
            msg = email.message_from_bytes(raw_email[1])
        else:
            logging.error(f"Unerwartetes Format für E-Mail ID {email_id_str}")
            return

        # Extrahiere Metadaten
        sender = email.utils.parseaddr(msg.get("From", ""))[1] or "Unbekannt"
        subject = decode_header_safe(msg.get("Subject", "Kein Betreff"))
        body_preview = extract_body_preview(msg)

        # Ausgabe
        print(f"\n📧 Von: {sender}")
        print(
            f"   Betreff: {subject[:MAX_SUBJECT_LENGTH]}{'...' if len(subject) > MAX_SUBJECT_LENGTH else ''}"
        )

        # LLM-Analyse
        is_spam, reason = detect_spam(
            sender, subject, body_preview, list_manager=list_manager
        )

        if is_spam:
            print(f"   ❌ SPAM: {reason[:100]}")

            # Verschiebe zu Spam-Ordner
            try:
                mail.copy(email_id_str, account["spam_folder"])
                mail.store(email_id_str, "+FLAGS", "\\Deleted")
                logging.info(
                    f"SPAM verschoben: {subject} von {sender} ({account['name']})"
                )

                # Sammle Absender für Übersicht
                if isinstance(stats["spam_senders"], list):
                    stats["spam_senders"].append(
                        {"email": sender, "subject": subject, "reason": reason}
                    )
            except Exception as e:
                logging.error(f"Spam-Verschiebung fehlgeschlagen: {e}")
                print(f"   ⚠️  Verschiebung fehlgeschlagen: {e}")

            if isinstance(stats["spam"], int):
                stats["spam"] += 1
        else:
            print(f"   ✅ HAM: {reason[:100]}")

            # Markiere als gelesen
            mail.store(email_id_str, "+FLAGS", "\\Seen")
            logging.info(f"HAM behalten: {subject} ({account['name']})")

            if isinstance(stats["ham"], int):
                stats["ham"] += 1

    except Exception as e:
        logging.error(f"Fehler bei E-Mail ID {email_id!r}: {e}", exc_info=True)
        print(f"\n⚠️  Fehler bei dieser E-Mail: {e}")


def process_inbox(
    account: Dict[str, str], list_manager: Optional[ListManager] = None
) -> Dict[str, Any]:
    """
    Hauptfunktion: Verarbeitet INBOX und filtert Spam.

    Args:
        account: Account-Konfiguration
        list_manager: Optionaler ListManager

    Returns:
        Dict mit Statistiken: {'spam': int, 'ham': int, 'spam_senders': list}
    """
    try:
        mail = connect_imap(account)
    except Exception as e:
        logging.error(f"Verbindung zu {account['name']} fehlgeschlagen: {e}")
        print(f"\n⚠️  Überspringe {account['name']} (Verbindung fehlgeschlagen)\n")
        return {"spam": 0, "ham": 0, "spam_senders": [], "error": True}

    stats = {"spam": 0, "ham": 0, "spam_senders": [], "error": False}

    try:
        # Suche E-Mails basierend auf Filter-Modus
        if FILTER_MODE == "days":
            # Berechne Datum für IMAP-Suche
            since_date = datetime.now() - timedelta(days=DAYS_BACK)
            date_str = since_date.strftime("%d-%b-%Y")  # Format: "19-Nov-2025"

            print(f"\n🔍 Suche E-Mails seit {date_str} (letzte {DAYS_BACK} Tage)...")
            status, data = mail.search(None, f"(SINCE {date_str})")

            if status != "OK":
                logging.error("IMAP SEARCH fehlgeschlagen")
                print("❌ E-Mail-Suche fehlgeschlagen")
                return stats

            email_ids = data[0].split()

        else:  # FILTER_MODE == 'count'
            print(f"\n🔍 Suche letzte {LIMIT} E-Mails...")
            status, data = mail.search(None, "ALL")

            if status != "OK":
                logging.error("IMAP SEARCH fehlgeschlagen")
                print("❌ E-Mail-Suche fehlgeschlagen")
                return stats

            email_ids = data[0].split()

            # Limit anwenden (neueste E-Mails = höchste IDs)
            email_ids = email_ids[-LIMIT:] if len(email_ids) > LIMIT else email_ids

        if not email_ids:
            if FILTER_MODE == "days":
                print(f"✅ Keine E-Mails in den letzten {DAYS_BACK} Tagen gefunden!")
            else:
                print("✅ Keine E-Mails gefunden!")
            return stats

        print(f"📧 Analysiere {len(email_ids)} E-Mail(s)...\n")

        # Verarbeite E-Mails mit Progress-Bar
        for email_id in tqdm(email_ids, desc="Verarbeite E-Mails", unit="mail"):
            _process_single_email(mail, email_id, account, list_manager, stats)

        return stats

    finally:
        # Cleanup
        try:
            print("\n🧹 Räume auf...")
            mail.expunge()  # Lösche markierte E-Mails
            mail.logout()
            print("✅ IMAP-Verbindung geschlossen")

        except Exception as e:
            logging.error(f"Logout fehlgeschlagen: {e}", exc_info=True)


# ============================================
# Main Entry Point
# ============================================


def _check_ollama_availability() -> bool:
    """Prüft ob Ollama und das Modell verfügbar sind."""
    print("🔍 Prüfe Ollama-Verfügbarkeit...")
    try:
        response = requests.get(
            "http://localhost:11434/api/tags", timeout=OLLAMA_CHECK_TIMEOUT
        )
        if response.status_code == HTTP_OK:
            print("✅ Ollama läuft")

            # Prüfe ob Modell verfügbar ist
            print(f"🔍 Prüfe LLM-Modell '{SPAM_MODEL}'...")
            models_data = response.json()
            available_models = [
                model["name"] for model in models_data.get("models", [])
            ]

            if SPAM_MODEL in available_models:
                print(f"✅ Modell '{SPAM_MODEL}' ist verfügbar")
            else:
                print(f"⚠️  Modell '{SPAM_MODEL}' nicht gefunden!")
                print(
                    f"   Verfügbare Modelle: {', '.join(available_models) if available_models else 'keine'}"
                )
                print(f"   Installation: ollama pull {SPAM_MODEL}")
                print("\n⏹️  Script wird abgebrochen.\n")
                logging.error(
                    f"LLM-Modell {SPAM_MODEL} nicht verfügbar - Script abgebrochen"
                )
                return False

            # Teste LLM mit einfacher Anfrage (Warm-up)
            print(f"🚀 Starte LLM '{SPAM_MODEL}'...")
            print(
                "   ⏳ Bitte warten, Modell wird geladen (beim ersten Aufruf kann das etwas dauern)..."
            )

            try:
                warmup_response = requests.post(
                    OLLAMA_URL,
                    json={
                        "model": SPAM_MODEL,
                        "prompt": "Test",
                        "stream": False,
                        "options": {"num_predict": 1},
                    },
                    timeout=LLM_WARMUP_TIMEOUT,
                )
                warmup_response.raise_for_status()
                print(f"✅ LLM '{SPAM_MODEL}' ist einsatzbereit!\n")
                logging.info(f"LLM {SPAM_MODEL} erfolgreich initialisiert")
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
        else:
            print("⚠️  Ollama antwortet nicht wie erwartet\n")
            return False
    except requests.ConnectionError:
        print("❌ Ollama nicht erreichbar!")
        print("   Starte in anderem Terminal: ollama serve")
        print("   (Oder als Dienst: brew services start ollama)")
        print("   Details: docs/SETUP.md → Abschnitt 'Ollama einrichten'")
        print("\n⏹️  Script wird abgebrochen - keine E-Mails verarbeitet.\n")
        logging.error("Ollama nicht erreichbar - Script abgebrochen")
        return False


def _print_summary(total_stats: Dict[str, Any]) -> None:
    """Gibt die Zusammenfassung aus."""
    total = total_stats["spam"] + total_stats["ham"]
    print("\n" + "=" * 60)
    print("📊 Gesamtzusammenfassung")
    print("=" * 60)
    print(
        f"   Accounts verarbeitet: {total_stats['accounts_processed']}/{len(EMAIL_ACCOUNTS)}"
    )

    if total_stats["accounts_failed"] > 0:
        print(f"   ⚠️  Accounts fehlgeschlagen: {total_stats['accounts_failed']}")

    print(f"   Gesamt analysiert: {total} E-Mails")
    print(f"   ❌ Als SPAM erkannt: {total_stats['spam']}")
    print(f"   ✅ Als HAM erkannt: {total_stats['ham']}")

    if total > 0:
        spam_rate = (total_stats["spam"] / total) * 100
        print(f"   📈 Gesamt-Spam-Rate: {spam_rate:.1f}%")

    # Zeige Spam-Absender Übersicht (Global)
    if total_stats.get("spam_senders"):
        print("\n" + "=" * 60)
        print(
            f"🚫 SPAM-ABSENDER ÜBERSICHT ({len(total_stats['spam_senders'])} E-Mails verschoben)"
        )
        print("=" * 60)

        # Gruppiere nach E-Mail-Adresse
        senders_grouped = defaultdict(list)
        for spam_mail in total_stats["spam_senders"]:
            senders_grouped[spam_mail["email"]].append(spam_mail["subject"])

        for sender_email, subjects in sorted(senders_grouped.items()):
            print(f"\n📧 {sender_email} ({len(subjects)} E-Mail(s))")
            for subject in subjects[:MAX_SUBJECTS_TO_SHOW]:
                print(
                    f"   • {subject[:MAX_SUMMARY_SUBJECT_LENGTH]}{'...' if len(subject) > MAX_SUMMARY_SUBJECT_LENGTH else ''}"
                )
            if len(subjects) > MAX_SUBJECTS_TO_SHOW:
                print(f"   ... und {len(subjects) - MAX_SUBJECTS_TO_SHOW} weitere")

        print("\n" + "=" * 60)
        print("💡 TIPP: Falls eine E-Mail-Adresse fälschlich blockiert wurde:")
        print("   1. Füge sie zur Whitelist hinzu: data/lists/whitelist.txt")
        print("   2. Stelle E-Mails wieder her: make unspam")
        print("=" * 60)

    print(f"\n   📄 Details: {LOG_PATH}")
    print("=" * 60 + "\n")


def main():
    """Hauptfunktion des Spam-Filters mit Multi-Account Support."""

    print("\n" + "=" * 60)
    print("🤖 LLM-basierter IMAP Spam-Filter (Multi-Account)")
    print("=" * 60)
    print(f"   Modell: {SPAM_MODEL}")
    print(f"   Accounts: {len(EMAIL_ACCOUNTS)}")

    if FILTER_MODE == "days":
        print(f"   Filter: Letzte {DAYS_BACK} Tage")
    else:
        print(f"   Filter: Letzte {LIMIT} E-Mails pro Account")

    print(f"   Log: {LOG_PATH}")
    print("=" * 60 + "\n")

    try:
        if not _check_ollama_availability():
            return

        # Initialisiere ListManager
        list_manager = create_list_manager()

        # Gesamtstatistik
        total_stats = {
            "spam": 0,
            "ham": 0,
            "accounts_processed": 0,
            "accounts_failed": 0,
            "spam_senders": [],
        }

        # Verarbeite alle Accounts
        for idx, account in enumerate(EMAIL_ACCOUNTS, 1):
            print("\n" + "─" * 60)
            print(f"📬 Account {idx}/{len(EMAIL_ACCOUNTS)}: {account['name']}")
            print(f"   Server: {account['server']}")
            print("─" * 60)

            # Verarbeite Account
            stats = process_inbox(account, list_manager=list_manager)

            if stats.get("error", False):
                total_stats["accounts_failed"] += 1
                continue

            # Aktualisiere Gesamtstatistik
            total_stats["spam"] += stats["spam"]
            total_stats["ham"] += stats["ham"]
            total_stats["accounts_processed"] += 1
            if stats.get("spam_senders"):
                total_stats["spam_senders"].extend(stats["spam_senders"])

            # Account-Statistik
            account_total = stats["spam"] + stats["ham"]
            if account_total > 0:
                spam_rate = (stats["spam"] / account_total) * 100
                print(
                    f"\n   📊 {account['name']}: {account_total} E-Mails ({stats['spam']} SPAM, {stats['ham']} HAM, {spam_rate:.1f}% Spam-Rate)"
                )

        _print_summary(total_stats)

    except KeyboardInterrupt:
        print("\n\n⏸️  Abbruch durch Benutzer")
        logging.info("Manueller Abbruch durch Benutzer")
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        logging.error(f"Unerwarteter Fehler: {e}", exc_info=True)
        print(f"\n💡 Details in: {LOG_PATH}")


if __name__ == "__main__":
    main()
