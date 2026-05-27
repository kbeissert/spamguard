#!/usr/bin/env python3
"""
Training Data Export Script

Exportiert Mails aus IMAP-Ordnern als .eml Dateien für Bayesian Training.

Workflow:
- export_spam: Liest Spam-Ordner → data/training/spam/*.eml
- export_ham: Liest Sent-Ordner (60%) + INBOX/Whitelist (40%) → data/training/ham/*.eml

Usage:
    python scripts/export_training_data.py spam --account 0 --limit 500
    python scripts/export_training_data.py ham --account 0 --limit 200
"""

import argparse
import email
import imaplib
import logging
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterator, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import EMAIL_ACCOUNTS, PROJECT_ROOT
from list_manager import ListManager

try:
    from tqdm import tqdm
except ImportError:
    # Fallback wenn tqdm nicht installiert
    def tqdm(iterable, desc=""):
        print(f"{desc}...")
        return iterable


@contextmanager
def imap_connection(account: Dict, folder: str = "INBOX") -> Iterator[imaplib.IMAP4_SSL]:
    """
    Context Manager für IMAP-Verbindung.

    Args:
        account: Account-Dict aus config
        folder: IMAP-Ordner (z.B. "INBOX", "Sent", account["spam_folder"])

    Yields:
        imaplib.IMAP4_SSL: Aktive IMAP-Verbindung
    """
    mail = None
    try:
        mail = imaplib.IMAP4_SSL(account["server"], account["port"])
        mail.login(account["user"], account["password"])
        mail.select(folder)
        logging.info(f"✅ Verbunden: {account['user']} → {folder}")
        yield mail
    except Exception as e:
        logging.error(f"IMAP-Verbindung fehlgeschlagen: {e}")
        raise
    finally:
        if mail:
            try:
                mail.logout()
            except Exception:
                pass


def export_spam_from_imap(account: Dict, limit: int = 500, days_back: int = 90):
    """
    Exportiert Spam-Mails aus IMAP Spam-Ordner.

    Args:
        account: Account-Dict aus config
        limit: Maximale Anzahl Mails
        days_back: Zeitraum in Tagen (Standard: 90)
    """
    spam_path = PROJECT_ROOT / "data" / "training" / "spam"
    spam_path.mkdir(parents=True, exist_ok=True)

    print(f"\n📧 Exportiere Spam-Mails aus: {account['name']}")
    print(f"   Ordner: {account['spam_folder']}")
    print(f"   Zeitraum: Letzte {days_back} Tage")
    print(f"   Limit: {limit} Mails")

    try:
        with imap_connection(account, account["spam_folder"]) as mail:
            # Suche Mails der letzten N Tage
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            status, data = mail.search(None, f"SINCE {since_date}")

            if status != "OK":
                print(f"❌ Suche fehlgeschlagen: {status}")
                return

            email_ids = data[0].split()
            total = len(email_ids)

            if total == 0:
                print(f"⚠️  Keine Spam-Mails gefunden im Zeitraum")
                return

            print(f"   Gefunden: {total} Mails")

            # Begrenze auf limit
            email_ids = email_ids[:limit]
            print(f"   Exportiere: {len(email_ids)} Mails")

            # Exportiere .eml Dateien
            exported = 0
            for idx, email_id in enumerate(tqdm(email_ids, desc="Export Spam")):
                try:
                    status, msg_data = mail.fetch(email_id, "(RFC822)")
                    if status != "OK":
                        continue

                    eml_content = msg_data[0][1]
                    filename = spam_path / f"spam_{idx:04d}.eml"
                    filename.write_bytes(eml_content)
                    exported += 1

                except Exception as e:
                    logging.warning(f"Fehler bei Mail {email_id}: {e}")
                    continue

            print(f"\n✅ Spam-Export abgeschlossen: {exported}/{len(email_ids)} Mails → {spam_path}")

    except Exception as e:
        logging.error(f"Spam-Export fehlgeschlagen: {e}", exc_info=True)
        print(f"\n❌ Spam-Export fehlgeschlagen: {e}")


def export_ham_from_imap(account: Dict, limit: int = 200, days_back: int = 14):
    """
    Exportiert HAM-Mails aus zwei sicheren Quellen:
    1. Sent-Ordner (60% der Mails — 100% HAM, da selbst geschrieben)
    2. INBOX mit Whitelist-Filter (40% — nur bekannte Absender)

    Args:
        account: Account-Dict aus config
        limit: Maximale Anzahl Mails
        days_back: Zeitraum für INBOX-Suche (Standard: 14 Tage)
    """
    ham_path = PROJECT_ROOT / "data" / "training" / "ham"
    ham_path.mkdir(parents=True, exist_ok=True)

    print(f"\n📧 Exportiere HAM-Mails aus: {account['name']}")
    print(f"   Quellen: Sent (60%) + INBOX/Whitelist (40%)")
    print(f"   Limit: {limit} Mails")

    sent_limit = int(limit * 0.6)
    inbox_limit = int(limit * 0.4)

    # ========================================
    # Quelle 1: Sent-Ordner (primär)
    # ========================================
    sent_exported = 0
    try:
        print(f"\n📤 Lese Sent-Ordner (Ziel: {sent_limit} Mails)...")
        with imap_connection(account, "Sent") as mail:
            status, data = mail.search(None, "ALL")

            if status != "OK":
                print(f"⚠️  Sent-Ordner-Suche fehlgeschlagen: {status}")
            else:
                sent_ids = data[0].split()
                total_sent = len(sent_ids)

                if total_sent == 0:
                    print(f"⚠️  Keine Mails in Sent-Ordner gefunden")
                else:
                    print(f"   Gefunden: {total_sent} Mails")
                    sent_ids = sent_ids[:sent_limit]
                    print(f"   Exportiere: {len(sent_ids)} Mails")

                    for idx, email_id in enumerate(tqdm(sent_ids, desc="Export HAM (Sent)")):
                        try:
                            status, msg_data = mail.fetch(email_id, "(RFC822)")
                            if status != "OK":
                                continue

                            eml_content = msg_data[0][1]
                            filename = ham_path / f"ham_sent_{idx:04d}.eml"
                            filename.write_bytes(eml_content)
                            sent_exported += 1

                        except Exception as e:
                            logging.warning(f"Fehler bei Sent-Mail {email_id}: {e}")
                            continue

                    print(f"✅ Sent-Ordner: {sent_exported}/{len(sent_ids)} Mails exportiert")

    except Exception as e:
        logging.warning(f"Sent-Ordner nicht verfügbar: {e}")
        print(f"⚠️  Sent-Ordner nicht verfügbar — nutze nur INBOX")

    # ========================================
    # Quelle 2: INBOX + Whitelist-Filter
    # ========================================
    inbox_exported = 0
    try:
        print(f"\n📥 Lese INBOX mit Whitelist-Filter (Ziel: {inbox_limit} Mails)...")

        # Lade Whitelist
        list_manager = ListManager()
        whitelist = list_manager.whitelist

        if not whitelist:
            print(f"⚠️  Keine Whitelist vorhanden — überspringe INBOX-Export")
            print(f"   Lege Absender in data/lists/whitelist.txt an")
        else:
            print(f"   Whitelist: {len(whitelist)} Einträge")

            with imap_connection(account, "INBOX") as mail:
                # Suche gelesene Mails der letzten N Tage
                since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
                status, data = mail.search(None, f"SEEN SINCE {since_date}")

                if status != "OK":
                    print(f"⚠️  INBOX-Suche fehlgeschlagen: {status}")
                else:
                    inbox_ids = data[0].split()
                    total_inbox = len(inbox_ids)
                    print(f"   Gefunden: {total_inbox} gelesene Mails")

                    # Filtere nach Whitelist (nur Header fetchen für Performance)
                    filtered_ids = []
                    for email_id in tqdm(inbox_ids, desc="Filter Whitelist"):
                        try:
                            status, msg_data = mail.fetch(email_id, "(RFC822.HEADER)")
                            if status != "OK":
                                continue

                            msg = email.message_from_bytes(msg_data[0][1])
                            sender = email.utils.parseaddr(msg.get("From", ""))[1]

                            # Prüfe ob Sender auf Whitelist
                            if any(wl in sender for wl in whitelist):
                                filtered_ids.append(email_id)

                                if len(filtered_ids) >= inbox_limit:
                                    break

                        except Exception as e:
                            logging.warning(f"Fehler bei Header-Check {email_id}: {e}")
                            continue

                    print(f"   Nach Whitelist-Filter: {len(filtered_ids)} Mails")

                    if len(filtered_ids) == 0:
                        print(f"⚠️  Keine INBOX-Mails mit Whitelist-Absender gefunden")
                    else:
                        # Exportiere gefilterte Mails
                        for idx, email_id in enumerate(tqdm(filtered_ids, desc="Export HAM (INBOX)")):
                            try:
                                status, msg_data = mail.fetch(email_id, "(RFC822)")
                                if status != "OK":
                                    continue

                                eml_content = msg_data[0][1]
                                filename = ham_path / f"ham_inbox_{idx:04d}.eml"
                                filename.write_bytes(eml_content)
                                inbox_exported += 1

                            except Exception as e:
                                logging.warning(f"Fehler bei INBOX-Mail {email_id}: {e}")
                                continue

                        print(f"✅ INBOX: {inbox_exported}/{len(filtered_ids)} Mails exportiert")

    except Exception as e:
        logging.error(f"INBOX-Export fehlgeschlagen: {e}", exc_info=True)
        print(f"⚠️  INBOX-Export fehlgeschlagen: {e}")

    # ========================================
    # Zusammenfassung
    # ========================================
    total_exported = sent_exported + inbox_exported
    print(f"\n✅ HAM-Export abgeschlossen: {total_exported}/{limit} Mails → {ham_path}")
    print(f"   Sent-Ordner: {sent_exported}")
    print(f"   INBOX/Whitelist: {inbox_exported}")


def main():
    """Hauptfunktion: CLI-Interface für Spam/HAM Export."""
    parser = argparse.ArgumentParser(
        description="Export Training Data aus IMAP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python scripts/export_training_data.py spam --account 0 --limit 500
  python scripts/export_training_data.py ham --account 0 --limit 200
  python scripts/export_training_data.py spam --account 1 --days 60
        """
    )

    parser.add_argument(
        "mode",
        choices=["spam", "ham"],
        help="Export-Modus: spam oder ham"
    )
    parser.add_argument(
        "--account",
        type=int,
        required=True,
        help="Account-Index aus accounts.yaml (z.B. 0, 1, 2)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximale Anzahl Mails (Default: spam=500, ham=200)"
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Zeitraum in Tagen (Default: spam=90, ham=14)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Ausführliche Ausgabe"
    )

    args = parser.parse_args()

    # Logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    print("\n" + "=" * 60)
    print(f"📦 Training Data Export — {args.mode.upper()}")
    print("=" * 60)

    # Prüfe Account-Index
    if args.account >= len(EMAIL_ACCOUNTS):
        print(f"❌ Account-Index {args.account} ungültig")
        print(f"   Verfügbare Accounts: 0-{len(EMAIL_ACCOUNTS) - 1}")
        print("\nKonfigurierte Accounts:")
        for idx, acc in enumerate(EMAIL_ACCOUNTS):
            print(f"   [{idx}] {acc['name']} ({acc['user']})")
        sys.exit(1)

    account = EMAIL_ACCOUNTS[args.account]
    print(f"\n📧 Account: [{args.account}] {account['name']}")
    print(f"   E-Mail: {account['user']}")

    # Export
    try:
        if args.mode == "spam":
            limit = args.limit or 500
            days = args.days or 90
            export_spam_from_imap(account, limit=limit, days_back=days)

        elif args.mode == "ham":
            limit = args.limit or 200
            days = args.days or 14
            export_ham_from_imap(account, limit=limit, days_back=days)

        print("\n" + "=" * 60)
        print(f"🚀 Nächster Schritt: make train")
        print("=" * 60)

    except Exception as e:
        logging.error(f"Export fehlgeschlagen: {e}", exc_info=True)
        print(f"\n❌ Export fehlgeschlagen: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
