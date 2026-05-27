#!/usr/bin/env python3
"""
Listen Audit - Interaktive Verwaltung von Whitelist und Blacklist

Zeigt alle Einträge nummeriert an und erlaubt pro Eintrag:
  - Entfernen aus der Liste
  - Auf die andere Liste verschieben
  - Mails direkt aus dem Spam-Ordner zurückholen (Unspam)

Usage:
    python audit_lists.py              # Fragt welche Liste
    python audit_lists.py --whitelist  # Direkt Whitelist
    python audit_lists.py --blacklist  # Direkt Blacklist
"""

import sys
import email
import logging
import argparse
from pathlib import Path
from typing import List, Tuple, Set

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import EMAIL_ACCOUNTS, LOG_PATH, WHITELIST_FILE as _WL, BLACKLIST_FILE as _BL, PROJECT_ROOT
from imap_utils import imap_connection
from utils import decode_header_safe

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

WHITELIST_FILE = PROJECT_ROOT / _WL
BLACKLIST_FILE = PROJECT_ROOT / _BL

SEP = "═" * 56
MAX_SUBJECT = 52


# ---------------------------------------------------------------------------
# Datei-Operationen (minimale Reimplementierung um manage_lists nicht zu importieren)
# ---------------------------------------------------------------------------

def _read_entries(list_type: str) -> Set[str]:
    file_path = WHITELIST_FILE if list_type == "whitelist" else BLACKLIST_FILE
    if not file_path.exists():
        return set()
    entries: Set[str] = set()
    for line in file_path.read_text(encoding="utf-8").splitlines():
        cleaned = line.split("#")[0].strip()
        if cleaned:
            entries.add(cleaned.lower())
    return entries


def _remove_entry(list_type: str, entry: str) -> None:
    file_path = WHITELIST_FILE if list_type == "whitelist" else BLACKLIST_FILE
    if not file_path.exists():
        return
    lines = file_path.read_text(encoding="utf-8").splitlines()
    new_lines = [l for l in lines if l.split("#")[0].strip().lower() != entry.lower()]
    file_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def _add_entry(list_type: str, entry: str) -> None:
    file_path = WHITELIST_FILE if list_type == "whitelist" else BLACKLIST_FILE
    file_path.parent.mkdir(parents=True, exist_ok=True)
    existing = _read_entries(list_type)
    if entry.lower() not in existing:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"{entry.lower()}\n")


# ---------------------------------------------------------------------------
# Unspam-Logik (eintrags-spezifisch)
# ---------------------------------------------------------------------------

def _restore_from_spam(query: str) -> int:
    """Stellt alle Mails von `query` (Adresse oder Domain) aus allen Spam-Ordnern wieder her."""
    query_lower = query.lower()
    total = 0

    for account in EMAIL_ACCOUNTS:
        try:
            with imap_connection(account, select_folder=account["spam_folder"]) as mail:
                status, data = mail.uid("search", None, "ALL")
                if status != "OK":
                    continue

                email_ids = data[0].split()
                if not email_ids:
                    continue

                to_restore = []
                for uid in email_ids:
                    try:
                        status, msg_data = mail.uid("fetch", uid, "(RFC822)")
                        if status != "OK":
                            continue
                        msg = email.message_from_bytes(msg_data[0][1])
                        sender = email.utils.parseaddr(msg.get("From", ""))[1].lower()
                        # Treffer bei exakter Adresse oder passender Domain
                        if sender == query_lower or sender.endswith(f"@{query_lower}"):
                            subject = decode_header_safe(msg.get("Subject", "Kein Betreff"))
                            to_restore.append((uid, sender, subject))
                    except Exception:
                        continue

                for uid, sender, subject in to_restore:
                    status, _ = mail.uid("copy", uid, "INBOX")
                    if status == "OK":
                        mail.uid("store", uid, "+FLAGS", "\\Deleted")
                        print(f"     ✅  {sender}: {subject[:MAX_SUBJECT]}")
                        logging.info(f"Audit/Unspam: {sender} ({account['name']})")
                        total += 1

        except Exception as e:
            print(f"     ❌  Fehler ({account['name']}): {e}")

    return total


# ---------------------------------------------------------------------------
# Nummerierte Eintrags-Liste
# ---------------------------------------------------------------------------

def _build_numbered(list_type: str) -> List[Tuple[int, str, str]]:
    """Gibt [(nr, entry, 'email'|'domain')] zurück."""
    entries = _read_entries(list_type)
    emails = sorted(e for e in entries if "@" in e)
    domains = sorted(e for e in entries if "@" not in e)
    result = []
    for e in emails:
        result.append((len(result) + 1, e, "email"))
    for d in domains:
        result.append((len(result) + 1, d, "domain"))
    return result


def _print_list(entries: List[Tuple[int, str, str]], list_type: str) -> None:
    label = "📋 WHITELIST" if list_type == "whitelist" else "🚫 BLACKLIST"
    print(f"\n{SEP}")
    print(f"  {label}  ({len(entries)} Einträge)")
    print(SEP)

    emails = [(n, e) for n, e, t in entries if t == "email"]
    domains = [(n, d) for n, d, t in entries if t == "domain"]

    if emails:
        print(f"\n  📧  E-Mail-Adressen ({len(emails)}):")
        for n, e in emails:
            print(f"    {n:>3}.  {e}")
    if domains:
        print(f"\n  🌐  Domains ({len(domains)}):")
        for n, d in domains:
            print(f"    {n:>3}.  {d}")

    print(f"\n{SEP}\n")


# ---------------------------------------------------------------------------
# Interaktives Menü pro Eintrag
# ---------------------------------------------------------------------------

def _handle_entry(entry: str, list_type: str) -> str:
    """Zeigt Aktionsmenü für einen Eintrag. Gibt 'continue' oder 'quit' zurück."""
    other = "blacklist" if list_type == "whitelist" else "whitelist"
    other_label = "Blacklist" if list_type == "whitelist" else "Whitelist"
    move_key = "b" if list_type == "whitelist" else "w"

    print(f"\n  ┌{'─' * 50}┐")
    print(f"  │  {entry:<48}  │")
    print(f"  └{'─' * 50}┘")

    print(f"\n  [R]  Entfernen")
    print(f"  [{move_key.upper()}]  Zur {other_label} verschieben")
    if list_type == "whitelist":
        print(f"  [U]  Unspam: Mails aus Spam-Ordner zurückholen")
    print(f"  [S]  Überspringen")
    print(f"  [Q]  Audit beenden")
    print()

    while True:
        choice = input("  Aktion: ").strip().lower()

        if choice == "s":
            return "continue"

        elif choice == "q":
            return "quit"

        elif choice == "r":
            _remove_entry(list_type, entry)
            print(f"\n  ✅  Entfernt: {entry}")
            return "continue"

        elif choice == move_key:
            _remove_entry(list_type, entry)
            _add_entry(other, entry)
            print(f"\n  ✅  Verschoben nach {other_label}: {entry}")
            return "continue"

        elif choice == "u" and list_type == "whitelist":
            print(f"\n  ♻️   Suche Mails von {entry} in allen Spam-Ordnern...")
            count = _restore_from_spam(entry)
            if count:
                print(f"\n  ✅  {count} E-Mail(s) zurückgeholt")
            else:
                print(f"  ℹ️   Keine Mails von {entry} im Spam-Ordner gefunden")
            return "continue"

        else:
            valid = "R / B / U / S / Q" if list_type == "whitelist" else "R / W / S / Q"
            print(f"  ❓  Ungültige Eingabe — bitte {valid}:")


# ---------------------------------------------------------------------------
# Auswahl-Loop für eine Liste
# ---------------------------------------------------------------------------

def _audit_list(list_type: str) -> None:
    entries = _build_numbered(list_type)
    if not entries:
        label = "Whitelist" if list_type == "whitelist" else "Blacklist"
        print(f"\n  ℹ️   {label} ist leer.\n")
        return

    _print_list(entries, list_type)

    print(f"  Eintrag auswählen:")
    print(f"  • Nummer eingeben (z.B.  3 )")
    print(f"  • Bereich eingeben (z.B.  1-5 )")
    print(f"  • [A] Alle der Reihe nach durchgehen")
    print(f"  • [Q] Beenden")

    while True:
        # Liste nach jeder Aktion neu aufbauen
        entries = _build_numbered(list_type)
        if not entries:
            print(f"\n  ✅  Liste ist jetzt leer.\n")
            break

        print()
        raw = input("  Auswahl: ").strip().lower()

        if raw in ("q", "quit"):
            break

        elif raw in ("a", "alle"):
            # Snapshot der aktuellen Einträge (Reihenfolge stabil)
            snapshot = [e for _, e, _ in _build_numbered(list_type)]
            for entry in snapshot:
                # Eintrag könnte zwischenzeitlich entfernt worden sein
                if entry not in _read_entries(list_type):
                    continue
                result = _handle_entry(entry, list_type)
                if result == "quit":
                    return
            # Liste nach Durchgang neu anzeigen
            entries = _build_numbered(list_type)
            if entries:
                _print_list(entries, list_type)

        elif "-" in raw:
            try:
                a, b = raw.split("-", 1)
                start, end = int(a.strip()), int(b.strip())
                snapshot = [e for n, e, _ in entries if start <= n <= end]
                if not snapshot:
                    print(f"  ❌  Kein Eintrag im Bereich {start}–{end}")
                    continue
                for entry in snapshot:
                    if entry not in _read_entries(list_type):
                        continue
                    result = _handle_entry(entry, list_type)
                    if result == "quit":
                        return
            except ValueError:
                print("  ❌  Ungültiger Bereich — Beispiel: 1-5")

        else:
            try:
                nr = int(raw)
                match = [e for n, e, _ in entries if n == nr]
                if not match:
                    print(f"  ❌  Kein Eintrag mit Nummer {nr}")
                    continue
                result = _handle_entry(match[0], list_type)
                if result == "quit":
                    break
            except ValueError:
                print("  ❌  Bitte Nummer, Bereich (1-5), A oder Q eingeben.")


# ---------------------------------------------------------------------------
# Listenauswahl
# ---------------------------------------------------------------------------

def _select_list() -> str:
    wl = len(_read_entries("whitelist"))
    bl = len(_read_entries("blacklist"))
    print(f"\n  Welche Liste prüfen?")
    print(f"  [W]  Whitelist  ({wl} Einträge)")
    print(f"  [B]  Blacklist  ({bl} Einträge)")
    print(f"  [A]  Beide")
    print()
    while True:
        choice = input("  Auswahl: ").strip().lower()
        if choice in ("w", "whitelist"):
            return "whitelist"
        elif choice in ("b", "blacklist"):
            return "blacklist"
        elif choice in ("a", "alle", "both"):
            return "both"
        else:
            print("  ❓  Bitte W, B oder A eingeben.")


# ---------------------------------------------------------------------------
# Einstiegspunkt
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interaktiver Audit für Whitelist und Blacklist"
    )
    parser.add_argument("--whitelist", action="store_true", help="Direkt Whitelist auditieren")
    parser.add_argument("--blacklist", action="store_true", help="Direkt Blacklist auditieren")
    args = parser.parse_args()

    print("\n╔" + "═" * 54 + "╗")
    print("║" + "  Spam Guard — Listen Audit".center(54) + "║")
    print("╚" + "═" * 54 + "╝")

    if args.whitelist:
        list_type = "whitelist"
    elif args.blacklist:
        list_type = "blacklist"
    else:
        list_type = _select_list()

    if list_type == "both":
        _audit_list("whitelist")
        _audit_list("blacklist")
    else:
        _audit_list(list_type)

    print("  ✅  Audit abgeschlossen.\n")


if __name__ == "__main__":
    main()
