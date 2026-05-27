#!/usr/bin/env python3
"""
Bayesian Filter Training Script

Trainiert den Bayesian Spam Filter aus .eml Dateien in data/training/{spam,ham,newsletter}/.

Workflow:
1. Liest alle .eml Dateien aus data/training/spam/, ham/ und optional newsletter/
2. Extrahiert Text-Features (Sender + Subject + Body)
3. Trainiert MultinomialNB mit CalibratedClassifierCV
4. Speichert Modell in data/models/bayesian_model.pkl

Modi:
- 2-Klassen: Nur spam/ und ham/ → HAM vs SPAM
- 3-Klassen: Zusätzlich newsletter/ → HAM vs SPAM vs NEWSLETTER

Usage:
    python scripts/train_bayesian.py                # Training
    python scripts/train_bayesian.py --stats        # Zeige Statistiken
    python scripts/train_bayesian.py --verbose      # Ausführliches Logging
"""

import argparse
import email
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bayesian_filter import BayesianFilter, extract_features
from config import (
    BAYESIAN_CONFIG,
    BAYESIAN_MODEL_PATH,
    BAYESIAN_VECTORIZER_PATH,
    PROJECT_ROOT,
)


def parse_eml_file(eml_path: Path) -> str:
    """
    Extrahiert Text aus .eml Datei für Training.

    Args:
        eml_path: Pfad zur .eml Datei

    Returns:
        str: Konkatenierter Text (Sender + Subject + Body)
    """
    try:
        with open(eml_path, 'rb') as f:
            msg = email.message_from_binary_file(f)

        # Extrahiere Sender und Subject
        sender = email.utils.parseaddr(msg.get('From', ''))[1] or ''
        subject = str(msg.get('Subject', '') or '')

        # Extrahiere Body (handle multipart)
        body = ''
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode('utf-8', errors='ignore')
                            break
                    except Exception:
                        continue
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode('utf-8', errors='ignore')
            except Exception:
                pass

        # Feature Engineering: Sender 3x für höheres TF-IDF Gewicht
        return extract_features(sender, subject, body)

    except Exception as e:
        logging.error(f"Fehler beim Parsen von {eml_path}: {e}")
        return ""


def load_training_data(data_dir: Path, verbose: bool = False) -> Tuple[List[str], List[str], List[str]]:
    """
    Lädt Training-Daten aus data/training/{spam,ham,newsletter}/.

    Args:
        data_dir: Root data/training/ Verzeichnis
        verbose: Ausführliche Ausgabe

    Returns:
        Tuple[List[str], List[str], List[str]]: (spam_texts, ham_texts, newsletter_texts)
    """
    spam_dir = data_dir / "spam"
    ham_dir = data_dir / "ham"
    newsletter_dir = data_dir / "newsletter"

    # Prüfe ob Verzeichnisse existieren
    if not spam_dir.exists():
        spam_dir.mkdir(parents=True, exist_ok=True)
        print(f"⚠️  Spam-Verzeichnis erstellt: {spam_dir}")
        print(f"   Lege .eml Dateien dort ab für Training.")

    if not ham_dir.exists():
        ham_dir.mkdir(parents=True, exist_ok=True)
        print(f"⚠️  HAM-Verzeichnis erstellt: {ham_dir}")
        print(f"   Lege .eml Dateien dort ab für Training.")

    # Newsletter-Ordner ist optional
    if not newsletter_dir.exists():
        if verbose:
            print(f"ℹ️  Newsletter-Verzeichnis existiert nicht: {newsletter_dir}")
            print(f"   Erstelle mit 'mkdir -p {newsletter_dir}' für 3-Klassen-Modus.")

    # Sammle .eml Dateien
    spam_files = list(spam_dir.glob("*.eml"))
    ham_files = list(ham_dir.glob("*.eml"))
    newsletter_files = list(newsletter_dir.glob("*.eml")) if newsletter_dir.exists() else []

    if not spam_files:
        print(f"\n❌ Keine Spam .eml Dateien gefunden in: {spam_dir}")
        print(f"   Lege mindestens 1 Spam-Mail als .eml Datei dort ab.")
        return [], [], []

    if not ham_files:
        print(f"\n❌ Keine HAM .eml Dateien gefunden in: {ham_dir}")
        print(f"   Lege mindestens 1 HAM-Mail als .eml Datei dort ab.")
        return [], [], []

    # Ausgabe: Zeige Modus (2-Klassen oder 3-Klassen)
    mode = "3-Klassen (HAM/SPAM/NEWSLETTER)" if newsletter_files else "2-Klassen (HAM/SPAM)"
    print(f"\n📂 Lese Training-Daten ({mode})...")
    print(f"   Spam: {len(spam_files)} Dateien")
    print(f"   HAM:  {len(ham_files)} Dateien")
    if newsletter_files:
        print(f"   Newsletter: {len(newsletter_files)} Dateien")

    # Parse .eml Dateien
    spam_texts = []
    ham_texts = []
    newsletter_texts = []

    for eml_file in spam_files:
        text = parse_eml_file(eml_file)
        if text:
            spam_texts.append(text)
            if verbose:
                print(f"   ✓ Spam: {eml_file.name}")

    for eml_file in ham_files:
        text = parse_eml_file(eml_file)
        if text:
            ham_texts.append(text)
            if verbose:
                print(f"   ✓ HAM:  {eml_file.name}")

    for eml_file in newsletter_files:
        text = parse_eml_file(eml_file)
        if text:
            newsletter_texts.append(text)
            if verbose:
                print(f"   ✓ Newsletter: {eml_file.name}")

    print(f"\n✅ Erfolgreich gelesen:")
    print(f"   Spam: {len(spam_texts)}/{len(spam_files)} Dateien")
    print(f"   HAM:  {len(ham_texts)}/{len(ham_files)} Dateien")
    if newsletter_files:
        print(f"   Newsletter: {len(newsletter_texts)}/{len(newsletter_files)} Dateien")

    return spam_texts, ham_texts, newsletter_texts


def save_metadata(data_dir: Path, stats: dict):
    """Speichert Training-Metadaten als JSON."""
    metadata = {
        "last_trained": datetime.now().isoformat(),
        "spam_count": stats["spam_count"],
        "ham_count": stats["ham_count"],
        "cv_folds": stats["cv_folds"],
        "feature_count": stats["feature_count"],
        "min_class_size": stats["min_class_size"],
        "warning": stats["warning"],
        "num_classes": stats["num_classes"],
    }

    # Newsletter nur bei 3-Klassen-Modus
    if stats["num_classes"] == 3:
        metadata["newsletter_count"] = stats.get("newsletter_count", 0)

    metadata_file = data_dir / "metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n📄 Metadaten gespeichert: {metadata_file}")


def show_stats(bayesian_filter: BayesianFilter, data_dir: Path):
    """Zeigt Training-Statistiken."""
    print("\n" + "=" * 60)
    print("📊 Bayesian Filter Statistics")
    print("=" * 60)

    stats = bayesian_filter.get_stats()

    if not stats.get("ready"):
        print("❌ Kein Modell trainiert — führe 'make train' aus")
        return

    print(f"✅ Modell bereit: {stats['model_path']}")
    print(f"   Vectorizer: {stats['vectorizer_path']}")
    print(f"   Modus: {stats.get('mode', '2-Klassen (HAM/SPAM)')}")
    print(f"   Features: {stats['feature_count']}")
    print(f"   Modell-Größe: {stats['model_size_bytes'] / 1024:.1f} KB")

    # Lade Metadaten
    metadata_file = data_dir / "metadata.json"
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        print(f"\n📅 Letztes Training: {metadata['last_trained']}")
        print(f"   Spam-Mails: {metadata['spam_count']}")
        print(f"   HAM-Mails: {metadata['ham_count']}")
        if metadata.get("num_classes") == 3:
            print(f"   Newsletter: {metadata.get('newsletter_count', 0)}")
        print(f"   CV Folds: {metadata['cv_folds']}")

        if metadata.get("warning"):
            print(f"\n⚠️  Niedrige Datenmenge — Ziel: 100+ Mails pro Kategorie")

    print("=" * 60)


def main():
    """Hauptfunktion: Training aus .eml Dateien."""
    parser = argparse.ArgumentParser(description="Bayesian Filter Training")
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Zeige Training-Statistiken (kein Training)"
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
    print("🤖 Bayesian Spam Filter - Training")
    print("=" * 60)

    # Initialisiere Filter
    bayesian_filter = BayesianFilter(
        model_path=BAYESIAN_MODEL_PATH,
        vectorizer_path=BAYESIAN_VECTORIZER_PATH
    )

    data_dir = PROJECT_ROOT / "data" / "training"

    # Stats-Modus
    if args.stats:
        show_stats(bayesian_filter, data_dir)
        return

    # Training-Modus
    spam_texts, ham_texts, newsletter_texts = load_training_data(data_dir, verbose=args.verbose)

    if not spam_texts or not ham_texts:
        print("\n❌ Training abgebrochen — zu wenig Daten")
        print("\nℹ️  Tipps:")
        print("   - Exportiere Mails: make export-spam && make export-ham")
        print("   - Oder: Nutze Starter-Samples: make train-with-starter")
        sys.exit(1)

    # Trainiere
    print(f"\n🤖 Starte Training...")
    min_samples_warning = BAYESIAN_CONFIG.get("bayesian", {}).get("training", {}).get("min_samples_warning", 100)

    try:
        stats = bayesian_filter.train_batch(
            spam_texts,
            ham_texts,
            newsletter_texts=newsletter_texts if newsletter_texts else None,
            min_samples_warning=min_samples_warning
        )

        print(f"\n✅ Training abgeschlossen!")
        mode = "3-Klassen" if stats["num_classes"] == 3 else "2-Klassen"
        print(f"   Modus: {mode}")
        print(f"   Spam: {stats['spam_count']} Mails")
        print(f"   HAM:  {stats['ham_count']} Mails")
        if stats["num_classes"] == 3:
            print(f"   Newsletter: {stats.get('newsletter_count', 0)} Mails")
        print(f"   CV Folds: {stats['cv_folds']}")
        print(f"   Features: {stats['feature_count']}")

        if stats["warning"]:
            print(f"\n⚠️  Hinweis: < {min_samples_warning} Mails pro Kategorie")
            print(f"   Genauigkeit kann < 85% sein")
            print(f"   Ziel: {min_samples_warning}+ pro Kategorie für beste Ergebnisse")

        # Speichere Metadaten
        save_metadata(data_dir, stats)

        print(f"\n💾 Modell gespeichert: {BAYESIAN_MODEL_PATH}")
        print(f"\n🚀 Jetzt: make start")
        print("=" * 60)

    except Exception as e:
        logging.error(f"Training fehlgeschlagen: {e}", exc_info=True)
        print(f"\n❌ Training fehlgeschlagen: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
