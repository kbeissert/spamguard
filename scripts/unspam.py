#!/usr/bin/env python3
"""
Unspam - Stellt fälschlich als Spam markierte E-Mails wieder her

Durchsucht Spam-Ordner nach E-Mails von Absendern auf der Whitelist
und verschiebt diese zurück in den Posteingang.

Usage:
    python unspam.py                    # Interaktiv: zeigt Vorschau
    python unspam.py --auto             # Automatisch: ohne Nachfrage
    python unspam.py --dry-run          # Nur anzeigen, nichts verschieben

Autor: Ollama Spam Guard
Datum: 2025-11-20
"""

import sys
import imaplib
import email
import logging
import argparse
from pathlib import Path
from typing import List, Dict

# Füge src/ zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import EMAIL_ACCOUNTS, LOG_PATH
from list_manager import get_list_manager
from utils import decode_header_safe

# Constants
MAX_SUBJECT_LENGTH = 60

# Logging
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def connect_imap(account: Dict[str, str]) -> imaplib.IMAP4_SSL:
    """
    Verbindet zum IMAP-Server.

    Args:
        account: Account-Konfiguration

    Returns:
        IMAP4_SSL: Verbundenes Mail-Objekt
    """
    mail = imaplib.IMAP4_SSL(account["server"], int(account["port"]))
    mail.login(account["user"], account["password"])
    return mail


def find_whitelisted_spam(account: Dict[str, str]) -> List[Dict]:
    """
    Durchsucht Spam-Ordner nach E-Mails von Whitelist-Absendern.

    Args:
        account: Account-Konfiguration

    Returns:
        List[Dict]: Gefundene E-Mails mit Metadaten
    """
    found_emails = []

    try:
        print(f"\n🔌 Verbinde zu {account['server']}...")
        mail = connect_imap(account)

        # Wähle Spam-Ordner
        print(f"📁 Öffne Spam-Ordner '{account['spam_folder']}'...")
        status, _ = mail.select(account["spam_folder"])

        if status != "OK":
            print(f"⚠️  Spam-Ordner '{account['spam_folder']}' nicht gefunden!")
            logging.warning(
                f"Spam-Ordner nicht gefunden: {account['spam_folder']} ({account['name']})"
            )
            return found_emails

        # Suche alle E-Mails im Spam-Ordner
        print("🔍 Durchsuche Spam-Ordner...")
        status, data = mail.search(None, "ALL")

        if status != "OK":
            print("❌ Suche fehlgeschlagen")
            return found_emails

        email_ids = data[0].split()

        if not email_ids:
            print("✅ Spam-Ordner ist leer")
            return found_emails

        print(f"📧 Prüfe {len(email_ids)} E-Mail(s) gegen Whitelist...\n")

        # Lade ListManager für Whitelist-Check
        list_manager = get_list_manager()

        # Prüfe jede E-Mail
        for email_id in email_ids:
            try:
                # Hole E-Mail
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                if status != "OK":
                    continue

                # Parse E-Mail
                msg = email.message_from_bytes(msg_data[0][1])

                # Extrahiere Absender
                sender = email.utils.parseaddr(msg.get("From", ""))[1] or "Unbekannt"
                subject = decode_header_safe(msg.get("Subject", "Kein Betreff"))
                date = msg.get("Date", "Unbekanntes Datum")

                # Prüfe gegen Whitelist
                is_spam, reason = list_manager.check_email(sender)

                # Nur wiederherstellen, wenn explizit auf der Whitelist!
                # check_email gibt (False, None) zurück, wenn die Mail weder auf White- noch Blacklist ist.
                if is_spam is False and reason and reason.startswith("Whitelist"):
                    print(f"✅ Gefunden: {sender}")
                    print(
                        f"   Betreff: {subject[:MAX_SUBJECT_LENGTH]}{'...' if len(subject) > MAX_SUBJECT_LENGTH else ''}"
                    )
                    print(f"   Grund: {reason}")

                    found_emails.append(
                        {
                            "id": email_id,
                            "sender": sender,
                            "subject": subject,
                            "date": date,
                            "reason": reason,
                        }
                    )

            except Exception as e:
                logging.error(f"Fehler beim Prüfen von E-Mail ID {email_id}: {e}")
                continue

        mail.close()
        mail.logout()

    except Exception as e:
        print(f"❌ Fehler: {e}")
        logging.error(
            f"Fehler bei find_whitelisted_spam ({account['name']}): {e}", exc_info=True
        )

    return found_emails


def restore_emails(account: Dict[str, str], emails: List[Dict]) -> int:
    """
    Verschiebt E-Mails zurück in den Posteingang.

    Args:
        account: Account-Konfiguration
        emails: Liste von E-Mails zum Wiederherstellen

    Returns:
        int: Anzahl wiederhergestellter E-Mails
    """
    if not emails:
        return 0

    restored_count = 0

    try:
        print(f"\n🔄 Stelle {len(emails)} E-Mail(s) wieder her...\n")
        mail = connect_imap(account)

        # Wähle Spam-Ordner
        mail.select(account["spam_folder"])

        for email_data in emails:
            try:
                email_id = email_data["id"]

                # Kopiere zurück in INBOX
                status, _ = mail.copy(email_id, "INBOX")

                if status == "OK":
                    # Lösche aus Spam-Ordner
                    mail.store(email_id, "+FLAGS", "\\Deleted")

                    print(f"✅ Wiederhergestellt: {email_data['sender']}")
                    print(
                        f"   Betreff: {email_data['subject'][:MAX_SUBJECT_LENGTH]}{'...' if len(email_data['subject']) > MAX_SUBJECT_LENGTH else ''}"
                    )

                    logging.info(
                        f"E-Mail wiederhergestellt: {email_data['subject']} von {email_data['sender']} ({account['name']})"
                    )
                    restored_count += 1
                else:
                    print(f"⚠️  Fehler bei: {email_data['sender']}")

            except Exception as e:
                print(f"❌ Fehler bei {email_data['sender']}: {e}")
                logging.error(f"Fehler beim Wiederherstellen: {e}")

        # Cleanup
        mail.expunge()
        mail.close()
        mail.logout()

    except Exception as e:
        print(f"❌ Fehler: {e}")
        logging.error(
            f"Fehler bei restore_emails ({account['name']}): {e}", exc_info=True
        )

    return restored_count


def _add_to_whitelist(email_to_add: str) -> None:
    """Fügt eine E-Mail-Adresse zur Whitelist hinzu."""
    whitelist_path = Path(__file__).parent.parent / "data" / "lists" / "whitelist.txt"
    try:
        # Prüfe ob bereits vorhanden
        if whitelist_path.exists():
            content = whitelist_path.read_text(encoding="utf-8")
            if email_to_add in content:
                print(f"ℹ️  {email_to_add} ist bereits auf der Whitelist.")
                return

        # Füge hinzu
        with whitelist_path.open("a", encoding="utf-8") as f:
            f.write(f"\n{email_to_add}")
        print(f"✅ {email_to_add} zur Whitelist hinzugefügt.")

        # Reload ListManager
        get_list_manager().load_all_lists(force_update=False)

    except Exception as e:
        print(f"❌ Fehler beim Schreiben der Whitelist: {e}")


def _process_account(account: Dict[str, str], auto: bool, dry_run: bool) -> None:
    """Verarbeitet einen einzelnen Account."""
    print("\n" + "─" * 60)
    print(f"📬 Account: {account['name']}")
    print("─" * 60)

    # 1. Suche Whitelisted E-Mails im Spam-Ordner
    found_emails = find_whitelisted_spam(account)

    if not found_emails:
        print("✅ Keine fälschlich markierten E-Mails gefunden.")
        return

    # 2. Wiederherstellen
    if dry_run:
        print(f"\n🔍 Dry-Run: Würde {len(found_emails)} E-Mail(s) wiederherstellen.")
    elif auto:
        restore_emails(account, found_emails)
    else:
        # Interaktive Abfrage
        print(f"\n❓ {len(found_emails)} E-Mail(s) wiederherstellen? (j/n)")
        choice = input("> ").lower()
        if choice in ["j", "y", "ja", "yes"]:
            restore_emails(account, found_emails)
        else:
            print("⏹️  Abgebrochen.")


def main():
    """Hauptfunktion des Unspam-Tools."""

    parser = argparse.ArgumentParser(
        description="Stellt fälschlich als Spam markierte E-Mails wieder her"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Automatisch wiederherstellen ohne Nachfrage",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Nur anzeigen, nichts verschieben"
    )
    parser.add_argument(
        "email",
        nargs="?",
        help="E-Mail-Adresse zur Whitelist hinzufügen und wiederherstellen",
    )
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("♻️  Unspam - E-Mail Wiederherstellung")
    print("=" * 60)

    # Wenn E-Mail übergeben wurde, zur Whitelist hinzufügen
    if args.email:
        _add_to_whitelist(args.email.strip().lower())

    print(f"   Accounts: {len(EMAIL_ACCOUNTS)}")

    if args.dry_run:
        print("   Modus: DRY RUN (keine Änderungen)")
    elif args.auto:
        print("   Modus: AUTOMATISCH")
    else:
        print("   Modus: INTERAKTIV")

    print("=" * 60)

    # Verarbeite alle Accounts
    for account in EMAIL_ACCOUNTS:
        _process_account(account, args.auto, args.dry_run)

    print("\n" + "=" * 60)
    print("✅ Fertig.")
    print("=" * 60 + "\n")




if __name__ == "__main__":
    main()
