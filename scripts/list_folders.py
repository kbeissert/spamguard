#!/usr/bin/env python3
"""
Spam Guard - IMAP Ordnerstruktur anzeigen

Listet alle verfügbaren Ordner für konfigurierte E-Mail-Accounts auf.
Hilfreich zum Finden des richtigen Spam-Ordner-Namens.
"""

import imaplib
import sys
import re
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# .env laden
load_dotenv()

from config import EMAIL_ACCOUNTS
from imap_utils import imap_connection


def decode_folder_name(folder_bytes: bytes) -> str:
    """Dekodiert IMAP-Ordnernamen (unterstützt UTF-7 und UTF-8)"""
    try:
        # IMAP verwendet modified UTF-7 für Ordnernamen
        return folder_bytes.decode("utf-7")
    except (UnicodeDecodeError, ValueError):
        try:
            return folder_bytes.decode("utf-8")
        except (UnicodeDecodeError, ValueError):
            return folder_bytes.decode("latin-1", errors="ignore")


def _parse_folder_name(folder_str: str) -> str:
    """Parses the folder name from the IMAP list response."""
    # Suche nach letztem Element nach dem Delimiter
    match = re.search(r'"\s+(.+)$', folder_str)
    if match:
        return match.group(1).strip('"')

    # Fallback
    parts = folder_str.split()
    return parts[-1].strip('"') if parts else "Unknown"


def _should_show_folder(folder_name: str, show_all: bool) -> bool:
    """Entscheidet, ob ein Ordner angezeigt werden soll."""
    if show_all:
        return True
    # Überspringe interne/versteckte Ordner
    return not (folder_name.startswith("[") or folder_name.startswith("."))


def _analyze_folders(
    mail: imaplib.IMAP4_SSL, account: Dict[str, str], show_all: bool
) -> Tuple[List[str], List[str], bool]:
    """Ruft Ordner ab und analysiert sie."""
    status, folders = mail.list()
    if status != "OK":
        print("❌ Fehler beim Abrufen der Ordner")
        return [], [], False

    configured_spam = account.get("spam_folder", "")
    spam_found = False
    folder_list = []
    potential_spam_folders = []

    for folder in folders:
        try:
            folder_str = folder.decode("utf-8", errors="ignore")
            folder_name = _parse_folder_name(folder_str)

            if not _should_show_folder(folder_name, show_all):
                continue

            folder_list.append(folder_name)

            if folder_name == configured_spam:
                spam_found = True

            spam_keywords = ["spam", "junk", "trash", "papierkorb", "gelöscht"]
            if any(keyword in folder_name.lower() for keyword in spam_keywords):
                potential_spam_folders.append(folder_name)

        except Exception:
            pass

    return folder_list, potential_spam_folders, spam_found


def list_folders(account: Dict[str, str], show_all: bool = False) -> bool:
    """
    Listet alle IMAP-Ordner eines Accounts auf

    Args:
        account: Account-Dictionary mit IMAP-Zugangsdaten
        show_all: Wenn True, zeigt auch System-Ordner
    """
    try:
        print(f"\n{'=' * 60}")
        print(f"  Account: {account['name']}")
        print(f"  Server: {account['server']}:{account['port']}")
        print(f"  User: {account['user']}")
        print(f"{'=' * 60}\n")

        # Use context manager for guaranteed cleanup (no folder selection)
        with imap_connection(account, select_folder=None) as mail:
            folder_list, _, spam_found = _analyze_folders(mail, account, show_all)
            configured_spam = account.get("spam_folder", "")

            if configured_spam and not spam_found:
                print("📁 Verfügbare Ordner:")
                print("-" * 60)

                for folder_name in folder_list:
                    spam_keywords = ["spam", "junk", "trash", "papierkorb", "gelöscht"]
                    marker = "⚠️  MÖGLICH" if any(k in folder_name.lower() for k in spam_keywords) else "  "
                    print(f"{marker:12} {folder_name}")

                print("-" * 60)
                print(f"📊 Gesamt: {len(folder_list)} Ordner gefunden\n")
            elif spam_found:
                print(f"✅ Spam-Ordner '{configured_spam}' gefunden\n")

            if configured_spam and not spam_found:
                print("=" * 60)
                print("⚠️  WARNUNG: Konfigurierter Spam-Ordner nicht gefunden!")
                print(f"   Gesucht: '{configured_spam}'")
                print("\n💡 Mögliche Spam-Ordner in der Liste oben (⚠️  MÖGLICH)")
                print("   Passe 'spam_folder' in accounts.yaml an!")
                print("=" * 60)

        return True

    except imaplib.IMAP4.error as e:
        print(f"❌ IMAP-Fehler: {e}")
        return False
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False


def _print_troubleshooting(failed_accounts: List[str], accounts: List[Dict[str, str]]) -> None:
    """Gibt Tipps zur Fehlerbehebung aus."""
    if not failed_accounts:
        return

    print(f"\n❌ Fehler bei folgenden Accounts: {', '.join(failed_accounts)}")
    print("\n💡 Tipps bei Login-Fehlern:")
    print("   - Prüfe Benutzername und Passwort in accounts.yaml")

    # Spezifische Tips basierend auf Provider
    for account_name in failed_accounts:
        account = next((a for a in accounts if a["name"] == account_name), None)
        if account:
            server = account.get("server", "").lower()
            if "gmail" in server:
                print(
                    f"   - {account_name}: App-Passwort erforderlich (nicht normales Passwort!)"
                )
            elif "outlook" in server or "hotmail" in server:
                print(f"   - {account_name}: Bei 2FA App-Passwort verwenden")
            elif "gmx" in server or "web.de" in server:
                print(f"   - {account_name}: IMAP in Einstellungen aktivieren")

    print("   - Stelle sicher, dass IMAP im E-Mail-Account aktiviert ist")


def main():
    """Hauptfunktion"""
    print("\n" + "=" * 60)
    print("  IMAP Ordnerstruktur anzeigen")
    print("=" * 60)

    # Argumente parsen
    show_all = "--all" in sys.argv or "-a" in sys.argv

    if show_all:
        print("\n💡 Zeige ALLE Ordner (inkl. System-Ordner)")

    # Accounts laden
    try:
        # EMAIL_ACCOUNTS ist bereits beim Import geladen
        accounts = EMAIL_ACCOUNTS
        print(f"\n📋 {len(accounts)} Account(s) konfiguriert")

        if not accounts:
            print("❌ Keine Accounts in accounts.yaml gefunden!")
            print("   Stelle sicher, dass mindestens ein Account enabled: true hat")
            return

    except Exception as e:
        print(f"❌ Fehler beim Laden der Accounts: {e}")
        return

    # Für jeden Account Ordner auflisten
    success_count = 0
    failed_accounts = []

    for i, account in enumerate(accounts, 1):
        result = list_folders(account, show_all)
        if result:
            success_count += 1
        else:
            failed_accounts.append(account["name"])

        # Pause zwischen Accounts (außer beim letzten)
        if i < len(accounts):
            input("\n⏸️  Drücke Enter für nächsten Account...")

    # Zusammenfassung
    print("\n" + "=" * 60)
    print(f"  Zusammenfassung: {success_count}/{len(accounts)} erfolgreich")
    print("=" * 60)

    _print_troubleshooting(failed_accounts, accounts)


if __name__ == "__main__":
    # Hilfe anzeigen
    if "--help" in sys.argv or "-h" in sys.argv:
        print("""
Verwendung: python list_folders.py [OPTIONEN]

Listet alle IMAP-Ordner der konfigurierten Accounts auf.

Optionen:
  -a, --all     Zeige auch System-Ordner (z.B. [Gmail]/...)
  -h, --help    Diese Hilfe anzeigen

Beispiele:
  python list_folders.py           # Standard (nur normale Ordner)
  python list_folders.py --all     # Alle Ordner inkl. System-Ordner

Hinweis:
  Das Script nutzt die Accounts aus accounts.yaml.
  Nur Accounts mit 'enabled: true' werden berücksichtigt.
        """)
        sys.exit(0)

    main()
