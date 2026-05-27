"""
SpamTrainer: Sammelt Spam-Samples automatisch während der Filterung
und löst Re-Training des Bayesian-Modells aus.

Strategie:
- Nur auto_*.eml Dateien werden gecappt/gedreht (manuelle Samples bleiben)
- Dedup via SHA256-Hash aus Betreff + ersten 200 Zeichen Body
- Re-Training via subprocess am Ende des Filter-Laufs
"""

import hashlib
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class SpamTrainer:
    def __init__(
        self,
        training_dir: Path,
        max_auto_samples: int = 500,
        retrain_every: int = 50,
    ):
        self.spam_dir = training_dir / "spam"
        self.spam_dir.mkdir(parents=True, exist_ok=True)
        self.max_auto_samples = max_auto_samples
        self.retrain_every = retrain_every
        self._added = 0

    def add_spam(self, sender: str, subject: str, body: str) -> bool:
        """
        Fügt Spam-Sample zu data/training/spam/ hinzu.
        Gibt True zurück wenn neu (kein Duplikat).
        """
        content_hash = self._hash(subject, body)
        target = self.spam_dir / f"auto_{content_hash}.eml"

        if target.exists():
            return False

        eml = (
            f"From: {sender}\n"
            f"Subject: {subject}\n"
            f"Date: {datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}\n"
            f"\n{body}"
        )
        target.write_text(eml, encoding="utf-8", errors="replace")
        self._added += 1
        self._prune()

        logging.info(f"Auto-Training: Sample gespeichert ({self._added} neu) — {subject[:60]}")
        return True

    def samples_added(self) -> int:
        return self._added

    def needs_retrain(self) -> bool:
        return self._added >= self.retrain_every

    def total_auto_samples(self) -> int:
        return len(list(self.spam_dir.glob("auto_*.eml")))

    def trigger_retrain(self, project_root: Path) -> bool:
        """Startet Re-Training via train_bayesian.py. Gibt True bei Erfolg."""
        train_script = project_root / "scripts" / "train_bayesian.py"
        if not train_script.exists():
            logging.error(f"train_bayesian.py nicht gefunden: {train_script}")
            return False

        print("\n" + "=" * 60)
        print("🔄 Auto-Training: Bayesian-Modell wird neu trainiert...")
        print("=" * 60)

        result = subprocess.run(
            [sys.executable, str(train_script)],
            cwd=str(project_root),
        )

        if result.returncode != 0:
            logging.error("Auto-Training fehlgeschlagen")
            print("⚠️  Re-Training fehlgeschlagen — führe 'make train' manuell aus.")
            return False

        logging.info("Auto-Training: Re-Training erfolgreich abgeschlossen")
        return True

    def _hash(self, subject: str, body: str) -> str:
        content = f"{subject}\n{body[:200]}"
        return hashlib.sha256(content.encode(errors="replace")).hexdigest()[:16]

    def _prune(self) -> None:
        samples = sorted(
            self.spam_dir.glob("auto_*.eml"),
            key=lambda p: p.stat().st_mtime,
        )
        while len(samples) > self.max_auto_samples:
            removed = samples.pop(0)
            removed.unlink()
            logging.info(f"Auto-Training: Ältestes Sample gelöscht — {removed.name}")
