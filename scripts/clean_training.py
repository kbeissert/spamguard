#!/usr/bin/env python3
"""
Clean Training Data - Entfernt Duplikate aus Training-Ordnern

Läuft automatisch vor make train.
Vergleicht Datei-Inhalte via MD5-Hash (nicht Dateinamen).

Usage:
    python scripts/clean_training.py
"""

import hashlib
import sys
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
TRAINING_DIR = PROJECT_ROOT / "data" / "training"

CATEGORIES = ["spam", "ham", "newsletter"]


def clean_category(folder: Path) -> tuple[int, int]:
    """
    Entfernt Duplikate aus einem Training-Ordner.

    Returns:
        (gesamt_vorher, anzahl_entfernt)
    """
    files = list(folder.glob("*.eml"))
    if not files:
        return 0, 0

    hashes = defaultdict(list)
    for f in files:
        try:
            h = hashlib.md5(f.read_bytes()).hexdigest()
            hashes[h].append(f)
        except Exception:
            continue

    to_delete = []
    for dupes in hashes.values():
        if len(dupes) > 1:
            # Behalte kürzesten Namen (Original), lösche den Rest
            dupes_sorted = sorted(dupes, key=lambda f: (len(f.name), f.name))
            to_delete.extend(dupes_sorted[1:])

    for f in to_delete:
        f.unlink()

    return len(files), len(to_delete)


def main():
    print("\n🧹 Bereinige Training-Daten...\n")

    total_removed = 0

    for category in CATEGORIES:
        folder = TRAINING_DIR / category
        if not folder.exists():
            continue

        vorher, entfernt = clean_category(folder)
        nachher = vorher - entfernt
        status = f"−{entfernt}" if entfernt > 0 else "✓"
        print(f"   {category.upper():<12} {vorher:4} → {nachher:4}  [{status}]")
        total_removed += entfernt

    if total_removed > 0:
        print(f"\n   {total_removed} Duplikate entfernt.")
    else:
        print(f"\n   Keine Duplikate gefunden.")

    print()


if __name__ == "__main__":
    main()
