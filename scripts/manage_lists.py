#!/usr/bin/env python3
"""
Listen-Verwaltung für Ollama Spam Guard
Vereinfachtes Tool zum Hinzufügen/Entfernen von E-Mails und Domains

Usage:
    python manage_lists.py whitelist add email@example.com
    python manage_lists.py whitelist add example.com
    python manage_lists.py whitelist remove email@example.com
    python manage_lists.py whitelist show

    python manage_lists.py blacklist add spam@bad.com
    python manage_lists.py blacklist remove spam@bad.com
    python manage_lists.py blacklist show

Autor: Ollama Spam Guard
Datum: 2025-11-20
"""

import sys
import argparse
from pathlib import Path
from typing import List, Set

# Füge src/ zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from constants import MAX_LIST_ENTRY_LENGTH  # noqa: E402

# Pfade zu Listen-Dateien
LISTS_DIR = Path(__file__).parent.parent / "data" / "lists"
WHITELIST_FILE = LISTS_DIR / "whitelist.txt"
BLACKLIST_FILE = LISTS_DIR / "blacklist.txt"


def ensure_file_exists(file_path: Path) -> None:
    """Erstellt Datei falls sie nicht existiert."""
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(
            f"# {file_path.stem}\n# Eine E-Mail oder Domain pro Zeile\n\n",
            encoding="utf-8",
        )
        print(f"✅ Datei erstellt: {file_path}")


def read_list(file_path: Path) -> List[str]:
    """Liest Liste und gibt alle Zeilen zurück (inkl. Kommentare für Datei-Erhalt)."""
    ensure_file_exists(file_path)

    lines = file_path.read_text(encoding="utf-8").splitlines()
    return lines


def get_entries_only(lines: List[str]) -> Set[str]:
    """Extrahiert nur die Einträge (ohne Kommentare und Leerzeilen)."""
    entries: Set[str] = set()
    for line in lines:
        cleaned = line.split("#")[0].strip()
        if cleaned:
            entries.add(cleaned.lower())
    return entries


def add_entry(list_type: str, entry: str) -> None:
    """Fügt Eintrag zur Liste hinzu."""
    file_path = WHITELIST_FILE if list_type == "whitelist" else BLACKLIST_FILE

    # Validiere Eintrag
    entry = entry.strip().lower()

    if not entry:
        print("❌ Fehler: Leerer Eintrag")
        sys.exit(1)

    if len(entry) > MAX_LIST_ENTRY_LENGTH:
        print(f"❌ Fehler: Eintrag zu lang (max {MAX_LIST_ENTRY_LENGTH} Zeichen)")
        sys.exit(1)

    # Prüfe ob bereits vorhanden
    lines = read_list(file_path)
    existing_entries = get_entries_only(lines)

    if entry in existing_entries:
        print(f"ℹ️  '{entry}' ist bereits auf der {list_type}")
        return

    # Füge hinzu
    ensure_file_exists(file_path)

    # Füge am Ende hinzu (nach letzter Zeile)
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"{entry}\n")

    print(f"✅ Hinzugefügt zur {list_type}: {entry}")

    # Zeige Tipp
    if list_type == "whitelist":
        print("💡 TIPP: Führe 'make unspam' aus um E-Mails wiederherzustellen")


def remove_entry(list_type: str, entry: str) -> None:
    """Entfernt Eintrag aus Liste."""
    file_path = WHITELIST_FILE if list_type == "whitelist" else BLACKLIST_FILE

    entry = entry.strip().lower()

    # Lese aktuelle Liste
    lines = read_list(file_path)
    existing_entries = get_entries_only(lines)

    if entry not in existing_entries:
        print(f"ℹ️  '{entry}' ist nicht auf der {list_type}")
        return

    # Filtere Eintrag raus
    new_lines = []
    removed = False

    for line in lines:
        cleaned = line.split("#")[0].strip()
        if cleaned.lower() == entry:
            removed = True
            continue  # Überspringe diese Zeile
        new_lines.append(line)

    # Schreibe zurück
    file_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    if removed:
        print(f"✅ Entfernt von {list_type}: {entry}")
    else:
        print(f"ℹ️  '{entry}' nicht gefunden")


def show_list(list_type: str) -> None:
    """Zeigt Liste an."""
    file_path = WHITELIST_FILE if list_type == "whitelist" else BLACKLIST_FILE

    ensure_file_exists(file_path)

    lines = read_list(file_path)
    entries = get_entries_only(lines)

    print(f"\n{'=' * 60}")
    print(f"📋 {list_type.upper()}")
    print(f"{'=' * 60}")

    if not entries:
        print("   (leer)")
    else:
        # Gruppiere nach E-Mail und Domain
        emails = sorted([e for e in entries if "@" in e])
        domains = sorted([e for e in entries if "@" not in e])

        if emails:
            print(f"\n📧 E-Mail-Adressen ({len(emails)}):")
            for email in emails:
                print(f"   • {email}")

        if domains:
            print(f"\n🌐 Domains ({len(domains)}):")
            for domain in domains:
                print(f"   • {domain}")

        print(f"\n📊 Gesamt: {len(entries)} Einträge")

    print(f"{'=' * 60}\n")
    print(f"📁 Datei: {file_path}")
    print()


def main():
    """Hauptfunktion."""
    parser = argparse.ArgumentParser(
        description="Verwalte Whitelist und Blacklist",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s whitelist add wichtig@firma.de    # E-Mail zur Whitelist
  %(prog)s whitelist add firma.de            # Domain zur Whitelist
  %(prog)s whitelist remove spam@bad.com     # Von Whitelist entfernen
  %(prog)s whitelist show                    # Whitelist anzeigen
  
  %(prog)s blacklist add spam@bad.com        # Zur Blacklist hinzufügen
  %(prog)s blacklist show                    # Blacklist anzeigen
        """,
    )

    parser.add_argument(
        "list_type", choices=["whitelist", "blacklist"], help="Welche Liste bearbeiten"
    )

    parser.add_argument(
        "action",
        choices=["add", "remove", "show"],
        help="Aktion (hinzufügen, entfernen, anzeigen)",
    )

    parser.add_argument("entry", nargs="?", help="E-Mail oder Domain (bei add/remove)")

    args = parser.parse_args()

    # Validierung
    if args.action in ["add", "remove"] and not args.entry:
        print(f"❌ Fehler: '{args.action}' benötigt eine E-Mail oder Domain")
        print(
            f"\nBeispiel: {sys.argv[0]} {args.list_type} {args.action} example@mail.com"
        )
        sys.exit(1)

    # Führe Aktion aus
    if args.action == "add":
        add_entry(args.list_type, args.entry)
    elif args.action == "remove":
        remove_entry(args.list_type, args.entry)
    elif args.action == "show":
        show_list(args.list_type)


if __name__ == "__main__":
    main()
