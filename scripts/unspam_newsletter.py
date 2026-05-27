#!/usr/bin/env python3
"""
Unspam-Newsletter - Verschiebt fälschlich als Spam markierte Newsletter

Durchsucht Spam-Ordner nach E-Mails von einem bestimmten Absender
und verschiebt diese in den Newsletter-Ordner.

Usage:
    python unspam_newsletter.py news@substack.com
    python unspam_newsletter.py substack.com
    python unspam_newsletter.py news@substack.com --dry-run

Autor: Spam Guard
"""

import email
import logging
import argparse
import sys
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import EMAIL_ACCOUNTS, LOG_PATH, NEWSLETTER_FOLDER
from utils import decode_header_safe
from imap_utils import imap_connection

MAX_SUBJECT_LENGTH = 60

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def find_sender_in_spam(account: Dict, sender_filter: str) -> List[Dict]:
    """
    Durchsucht Spam-Ordner nach E-Mails eines bestimmten Absenders.

    Args:
        account: Account-Konfiguration
        sender_filter: E-Mail-Adresse oder Domain (z.B. "news@sub.com" oder "sub.com")

    Returns:
        List[Dict]: Gefundene E-Mails
    """
    found_emails = []

    try:
        with imap_connection(account, select_folder=account["spam_folder"]) as mail:
            print(f"🔍 Durchsuche Spam-Ordner nach '{sender_filter}'...")
            status, data = mail.uid("search", None, "ALL")

            if status != "OK":
                print("❌ Suche fehlgeschlagen")
                return found_emails

            email_ids = data[0].split()

            if not email_ids:
                print("✅ Spam-Ordner ist leer")
                return found_emails

            print(f"📧 Prüfe {len(email_ids)} E-Mail(s)...\n")

            for email_id in email_ids:
                try:
                    status, msg_data = mail.uid("fetch", email_id, "(RFC822)")
                    if status != "OK":
                        continue

                    msg = email.message_from_bytes(msg_data[0][1])
                    sender = email.utils.parseaddr(msg.get("From", ""))[1] or ""
                    subject = decode_header_safe(msg.get("Subject", "Kein Betreff"))
                    date = msg.get("Date", "")

                    # Matche Adresse oder Domain
                    sender_lower = sender.lower()
                    filter_lower = sender_filter.lower()

                    is_match = (
                        sender_lower == filter_lower  # Exakte Adresse
                        or sender_lower.endswith(f"@{filter_lower}")  # Domain-Match
                        or sender_lower.endswith(f".{filter_lower}")  # Subdomain-Match
                    )

                    if is_match:
                        print(f"✅ Gefunden: {sender}")
                        print(f"   Betreff: {subject[:MAX_SUBJECT_LENGTH]}{'...' if len(subject) > MAX_SUBJECT_LENGTH else ''}")

                        found_emails.append({
                            "id": email_id,
                            "sender": sender,
                            "subject": subject,
                            "date": date,
                        })

                except Exception as e:
                    logging.error(f"Fehler beim Prüfen von E-Mail {email_id}: {e}")
                    continue

    except Exception as e:
        print(f"❌ Fehler: {e}")
        logging.error(f"Fehler bei find_sender_in_spam ({account['name']}): {e}", exc_info=True)

    return found_emails


def move_to_newsletter(account: Dict, emails: List[Dict], newsletter_folder: str) -> int:
    """
    Verschiebt E-Mails aus Spam in Newsletter-Ordner.

    Args:
        account: Account-Konfiguration
        emails: Zu verschiebende E-Mails
        newsletter_folder: Ziel-Ordner Name

    Returns:
        int: Anzahl verschobener E-Mails
    """
    if not emails:
        return 0

    moved_count = 0

    try:
        print(f"\n🔄 Verschiebe {len(emails)} E-Mail(s) → '{newsletter_folder}'...\n")

        with imap_connection(account, select_folder=account["spam_folder"]) as mail:
            for email_data in emails:
                try:
                    email_id = email_data["id"]
                    status, _ = mail.uid("copy", email_id, newsletter_folder)

                    if status == "OK":
                        mail.uid("store", email_id, "+FLAGS", "\\Deleted")
                        print(f"✅ Verschoben: {email_data['sender']}")
                        print(f"   Betreff: {email_data['subject'][:MAX_SUBJECT_LENGTH]}{'...' if len(email_data['subject']) > MAX_SUBJECT_LENGTH else ''}")
                        logging.info(f"Newsletter-Wiederherstellung: {email_data['subject']} von {email_data['sender']} → {newsletter_folder}")
                        moved_count += 1
                    else:
                        print(f"⚠️  Fehler bei: {email_data['sender']} (Ordner '{newsletter_folder}' vorhanden?)")

                except Exception as e:
                    print(f"❌ Fehler bei {email_data['sender']}: {e}")
                    logging.error(f"Fehler beim Verschieben: {e}")

    except Exception as e:
        print(f"❌ Fehler: {e}")
        logging.error(f"Fehler bei move_to_newsletter ({account['name']}): {e}", exc_info=True)

    return moved_count


def main():
    parser = argparse.ArgumentParser(
        description="Verschiebt fälschlich als Spam markierte Newsletter in Newsletter-Ordner"
    )
    parser.add_argument(
        "sender",
        help="E-Mail-Adresse oder Domain (z.B. news@substack.com oder substack.com)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur anzeigen, nichts verschieben",
    )
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("📂 Unspam-Newsletter - Newsletter Wiederherstellung")
    print("=" * 60)
    print(f"   Suche nach: {args.sender}")
    print(f"   Ziel-Ordner: {NEWSLETTER_FOLDER}")
    print(f"   Accounts: {len(EMAIL_ACCOUNTS)}")
    if args.dry_run:
        print("   Modus: DRY RUN (keine Änderungen)")
    print("=" * 60)

    total_moved = 0

    for account in EMAIL_ACCOUNTS:
        print(f"\n{'─' * 60}")
        print(f"📬 Account: {account['name']}")
        print("─" * 60)

        found = find_sender_in_spam(account, args.sender)

        if not found:
            print("✅ Keine Mails gefunden.")
            continue

        if args.dry_run:
            print(f"\n🔍 Dry-Run: Würde {len(found)} E-Mail(s) nach '{NEWSLETTER_FOLDER}' verschieben.")
        else:
            moved = move_to_newsletter(account, found, NEWSLETTER_FOLDER)
            total_moved += moved

    print("\n" + "=" * 60)
    if not args.dry_run:
        print(f"✅ Fertig: {total_moved} E-Mail(s) nach '{NEWSLETTER_FOLDER}' verschoben.")
        if total_moved > 0:
            print(f"\n💡 Tipp: Speichere eine .eml als Newsletter-Training:")
            print(f"   data/training/newsletter/ → make train")
    else:
        print("✅ Dry-Run abgeschlossen.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
