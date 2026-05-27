"""
Bayesian Spam Filter (scikit-learn)

Naive Bayes Klassifikator mit TF-IDF Features für schnelle Spam-Erkennung.
Trainiert auf .eml Dateien aus data/training/{spam,ham,newsletter}/.

Features:
- MultinomialNB mit CalibratedClassifierCV für realistische Probabilities
- Adaptive Cross-Validation (verhindert Crash bei wenig Daten)
- Retrain-Strategie: fit() auf alle Daten (kein partial_fit)
- Feature Engineering: Sender 3x gewichtet
- 3-Kategorie-Support: SPAM | HAM | NEWSLETTER (optional, backward compatible)

Workflow:
1. User legt .eml Dateien in data/training/{spam,ham,newsletter}/
2. `make train` trainiert Modell → data/models/bayesian_model.pkl
3. `predict_category()` liefert Kategorie + Probabilities
"""

import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB


class BayesianFilter:
    """
    Bayesian Spam Filter mit 2- oder 3-Kategorie-Support.

    Trainiert auf .eml Text-Dateien, liefert kalibrierte Kategorie-Scores.

    Kategorien:
    - 2-Klassen-Modus: HAM (0), SPAM (1)
    - 3-Klassen-Modus: HAM (0), SPAM (1), NEWSLETTER (2)
    """

    def __init__(
        self,
        model_path: Path,
        vectorizer_path: Optional[Path] = None,
        max_features: int = 5000
    ):
        """
        Args:
            model_path: Pfad zum gespeicherten Modell (.pkl)
            vectorizer_path: Optional separater Pfad für Vectorizer
            max_features: Max TF-IDF Features (Default: 5000)
        """
        self.model_path = Path(model_path)
        self.vectorizer_path = Path(vectorizer_path) if vectorizer_path else self.model_path.parent / "vectorizer.pkl"

        self.max_features = max_features

        # Custom Token-Pattern: Erkennt Email-Adressen und Domains als Ganzes
        # Pattern: email@domain.com | domain.com | word
        # Ohne dieses Pattern würde "spam@bad.xyz" zu ["spam", "bad", "xyz"] gesplittet
        token_pattern = r'(?u)\b[\w\.-]+@[\w\.-]+\b|\b[\w\.-]+\.[\w]+\b|\b\w\w+\b'

        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            token_pattern=token_pattern
        )
        self.classifier = None  # Wird bei train_batch() initialisiert

        self.num_classes = 2  # Default: 2-Klassen-Modus (HAM, SPAM)
        self.ready = False  # Flag: Modell trainiert und einsatzbereit
        self._load_or_init()

    def _load_or_init(self):
        """Lädt Modell von Disk oder initialisiert leer (Cold-Start)."""
        if self.model_path.exists() and self.vectorizer_path.exists():
            try:
                with open(self.vectorizer_path, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                with open(self.model_path, 'rb') as f:
                    self.classifier = pickle.load(f)

                # Backward Compatibility: Alte Modelle haben kein num_classes
                # Erkenne Modus anhand der Anzahl der Klassen im trainierten Modell
                if hasattr(self.classifier, 'classes_'):
                    self.num_classes = len(self.classifier.classes_)
                else:
                    # Fallback für sehr alte Modelle
                    self.num_classes = 2

                self.ready = True
                mode = "3-Klassen" if self.num_classes == 3 else "2-Klassen"
                logging.info(f"✅ Bayesian-Modell geladen: {self.model_path} ({mode})")
            except Exception as e:
                logging.error(f"Fehler beim Laden des Modells: {e}", exc_info=True)
                self.ready = False
        else:
            logging.warning(
                f"⚠️  Kein Bayesian-Modell gefunden: {self.model_path}\n"
                "   Führe 'make train' aus, um Bayesian-Filter zu aktivieren.\n"
                "   Bis dahin: LLM-Only-Modus (oder HAM-Default bei llm_fallback=false)"
            )
            self.ready = False

    def train_batch(
        self,
        spam_texts: List[str],
        ham_texts: List[str],
        newsletter_texts: Optional[List[str]] = None,
        min_samples_warning: int = 100
    ) -> Dict:
        """
        Trainiert Modell auf allen bereitgestellten Texten.

        WICHTIG: Retrain-Strategie — kein partial_fit().
        TF-IDF unterstützt kein inkrementelles Lernen, daher fit() auf alle Daten.

        Args:
            spam_texts: Liste von Spam-Texten (Sender + Subject + Body)
            ham_texts: Liste von HAM-Texten
            newsletter_texts: Optional Liste von Newsletter-Texten (3-Klassen-Modus)
            min_samples_warning: Warning bei weniger Samples

        Returns:
            Dict mit Training-Statistiken
        """
        if not spam_texts or not ham_texts:
            raise ValueError("Training benötigt mindestens 1 Spam + 1 HAM Mail")

        # Erkenne Modus: 2-Klassen (HAM/SPAM) oder 3-Klassen (HAM/SPAM/NEWSLETTER)
        if newsletter_texts and len(newsletter_texts) > 0:
            self.num_classes = 3
            all_texts = ham_texts + spam_texts + newsletter_texts
            labels = [0] * len(ham_texts) + [1] * len(spam_texts) + [2] * len(newsletter_texts)
            min_class = min(len(spam_texts), len(ham_texts), len(newsletter_texts))
        else:
            self.num_classes = 2
            all_texts = ham_texts + spam_texts
            labels = [0] * len(ham_texts) + [1] * len(spam_texts)
            min_class = min(len(spam_texts), len(ham_texts))

        # Adaptive Cross-Validation: cv=5 braucht mindestens 25 Samples pro Klasse
        # Bei weniger: cv=2 oder cv=3 (verhindert sklearn ValueError)
        cv_folds = min(5, max(2, min_class // 5))

        # Initialisiere Classifier mit adaptivem CV
        base_classifier = MultinomialNB()
        self.classifier = CalibratedClassifierCV(
            base_classifier,
            cv=cv_folds,        # Dynamisch: 2-5 Folds
            method='isotonic'   # Non-parametric calibration
        )

        # TF-IDF Feature Extraction (IMMER fit(), nie partial_fit())
        X = self.vectorizer.fit_transform(all_texts)

        # Train classifier
        self.classifier.fit(X, labels)

        self.ready = True

        # Logging & Warnings
        if self.num_classes == 3:
            logging.info(
                f"Training abgeschlossen: {len(ham_texts)} HAM + {len(spam_texts)} Spam + "
                f"{len(newsletter_texts)} Newsletter, cv={cv_folds}, "
                f"Features={len(self.vectorizer.get_feature_names_out())}"
            )
        else:
            logging.info(
                f"Training abgeschlossen: {len(spam_texts)} Spam + {len(ham_texts)} HAM, "
                f"cv={cv_folds}, Features={len(self.vectorizer.get_feature_names_out())}"
            )

        if min_class < min_samples_warning:
            logging.warning(
                f"⚠️  Niedrige Datenmenge ({min_class} pro Klasse) — "
                f"Genauigkeit < 85% erwartet. Ziel: {min_samples_warning}+ Mails pro Kategorie."
            )

        # Save to disk
        self._save()

        stats = {
            "ham_count": len(ham_texts),
            "spam_count": len(spam_texts),
            "cv_folds": cv_folds,
            "feature_count": len(self.vectorizer.get_feature_names_out()),
            "min_class_size": min_class,
            "warning": min_class < min_samples_warning,
            "num_classes": self.num_classes
        }

        if self.num_classes == 3:
            stats["newsletter_count"] = len(newsletter_texts)

        return stats

    def predict_score(self, text: str) -> float:
        """
        Liefert Spam-Probability (0.0-1.0) für gegebenen Text.

        BACKWARD COMPATIBILITY: Funktioniert nur im 2-Klassen-Modus.
        Im 3-Klassen-Modus nutze predict_category().

        Args:
            text: Email-Text (Sender + Subject + Body)

        Returns:
            float: Spam-Probability (0.0 = HAM, 1.0 = SPAM)
        """
        if not self.ready:
            logging.warning("Bayesian-Modell nicht bereit — Score=0.5 (neutral)")
            return 0.5  # Neutral → LLM-Fallback oder HAM-Default

        try:
            X = self.vectorizer.transform([text])
            proba = self.classifier.predict_proba(X)[0]

            if self.num_classes == 2:
                return proba[1]  # spam probability
            else:
                # 3-Klassen-Modus: Kombiniere SPAM + NEWSLETTER
                # (für Backward Compatibility mit altem Code)
                return proba[1] + proba[2]  # spam + newsletter
        except Exception as e:
            logging.error(f"Fehler bei predict_score(): {e}", exc_info=True)
            return 0.5  # Neutral bei Fehler

    def predict_category(self, text: str) -> Tuple[str, Dict[str, float]]:
        """
        Liefert Kategorie + Probabilities für gegebenen Text.

        Funktioniert in 2-Klassen und 3-Klassen-Modus.

        Args:
            text: Email-Text (Sender + Subject + Body)

        Returns:
            Tuple[str, Dict[str, float]]:
                - Kategorie: "HAM", "SPAM", oder "NEWSLETTER"
                - Probabilities: {"HAM": 0.x, "SPAM": 0.y, "NEWSLETTER": 0.z}
        """
        if not self.ready:
            logging.warning("Bayesian-Modell nicht bereit — Default HAM")
            if self.num_classes == 3:
                return ("HAM", {"HAM": 0.5, "SPAM": 0.25, "NEWSLETTER": 0.25})
            else:
                return ("HAM", {"HAM": 0.5, "SPAM": 0.5})

        try:
            X = self.vectorizer.transform([text])
            proba = self.classifier.predict_proba(X)[0]

            if self.num_classes == 2:
                # 2-Klassen-Modus: HAM (0) vs SPAM (1)
                category = "HAM" if proba[0] > proba[1] else "SPAM"
                proba_dict = {
                    "HAM": float(proba[0]),
                    "SPAM": float(proba[1])
                }
            else:
                # 3-Klassen-Modus: HAM (0) vs SPAM (1) vs NEWSLETTER (2)
                max_idx = proba.argmax()
                categories = ["HAM", "SPAM", "NEWSLETTER"]
                category = categories[max_idx]
                proba_dict = {
                    "HAM": float(proba[0]),
                    "SPAM": float(proba[1]),
                    "NEWSLETTER": float(proba[2])
                }

            return (category, proba_dict)

        except Exception as e:
            logging.error(f"Fehler bei predict_category(): {e}", exc_info=True)
            if self.num_classes == 3:
                return ("HAM", {"HAM": 0.5, "SPAM": 0.25, "NEWSLETTER": 0.25})
            else:
                return ("HAM", {"HAM": 0.5, "SPAM": 0.5})

    def get_stats(self) -> Dict:
        """
        Liefert Training-Statistiken.

        Returns:
            Dict mit Modell-Informationen
        """
        if not self.ready:
            return {
                "ready": False,
                "model_exists": False,
                "message": "Kein Modell trainiert — führe 'make train' aus"
            }

        mode = "3-Klassen (HAM/SPAM/NEWSLETTER)" if self.num_classes == 3 else "2-Klassen (HAM/SPAM)"

        return {
            "ready": True,
            "model_exists": True,
            "model_path": str(self.model_path),
            "vectorizer_path": str(self.vectorizer_path),
            "feature_count": len(self.vectorizer.get_feature_names_out()),
            "model_size_bytes": self.model_path.stat().st_size if self.model_path.exists() else 0,
            "num_classes": self.num_classes,
            "mode": mode
        }

    def _save(self):
        """Speichert Modell und Vectorizer auf Disk (pickle)."""
        try:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.vectorizer_path, 'wb') as f:
                pickle.dump(self.vectorizer, f)

            with open(self.model_path, 'wb') as f:
                pickle.dump(self.classifier, f)

            logging.info(f"Modell gespeichert: {self.model_path}")
        except Exception as e:
            logging.error(f"Fehler beim Speichern des Modells: {e}", exc_info=True)
            raise


def extract_features(sender: str, subject: str, body: str) -> str:
    """
    Feature Engineering für TF-IDF Vectorizer mit Spam-Signal-Erkennung.

    Extrahiert:
    - Sender 3x → höheres TF-Gewicht (exakte Absender-Matches)
    - Domain 3x → erkennt Spam-Domains (z.B. alle @spam-domain.xyz)
    - Subject 1x → Betreff-Keywords
    - Body (erste 1000 Zeichen) → Content-basierte Erkennung
    - Spam-Signale → CAPS, Sonderzeichen, URLs, Keywords

    Args:
        sender: Email-Absender (z.B. "spam@bad.com")
        subject: Email-Betreff
        body: Email-Body (Text)

    Returns:
        str: Konkatenierter Feature-String mit Spam-Signalen
    """
    import re

    # Extrahiere Domain aus Sender (z.B. "spam@bad.com" → "bad.com")
    domain = sender.split('@')[-1] if '@' in sender else sender

    # === Spam-Signal-Erkennung ===

    # 1. CAPS-Ratio: Anteil Großbuchstaben (GEWINN!!!, FREE!!!)
    combined_text = subject + " " + body[:1000]
    letters = [c for c in combined_text if c.isalpha()]
    caps_ratio = sum(1 for c in letters if c.isupper()) / len(letters) if letters else 0
    caps_signal = "HIGH_CAPS " * int(caps_ratio * 10) if caps_ratio > 0.3 else ""

    # 2. Sonderzeichen-Spam: $$$, !!!, ???, ✓✓✓
    special_chars = len(re.findall(r'[!$€£¥₹]{3,}', combined_text))
    special_signal = "SPECIAL_CHARS " * special_chars

    # 3. Exzessive Interpunktion: !!!, ???, ...
    excessive_punct = len(re.findall(r'[!?\.]{3,}', combined_text))
    punct_signal = "EXCESSIVE_PUNCT " * excessive_punct

    # 4. URL-Anzahl (viele URLs = oft Spam/Phishing)
    url_count = len(re.findall(r'https?://[^\s]+', combined_text))
    url_signal = "MANY_URLS " * min(url_count, 5)  # Cap bei 5

    # 5. Spam-Keywords (deutsch + englisch)
    spam_keywords = [
        'gewinn', 'gratis', 'kostenlos', 'viagra', 'bitcoin', 'krypto',
        'kredit', 'sofort', 'jetzt', 'klick', 'hier', 'angebot',
        'free', 'winner', 'congratulations', 'urgent', 'act now', 'limited',
        'casino', 'lottery', 'million', 'inheritance', 'prince'
    ]
    text_lower = combined_text.lower()
    keyword_hits = sum(1 for kw in spam_keywords if kw in text_lower)
    keyword_signal = "SPAM_KEYWORD " * min(keyword_hits, 5)  # Cap bei 5

    # Feature-Kombination:
    # - Sender 3x: Erkennt wiederkehrende exakte Adressen
    # - Domain 3x: Erkennt Spam-Domains (auch bei wechselnden Adressen)
    # - Subject: Keywords wie "Gewinn", "Viagra", etc.
    # - Body (first 1000 chars): Content-Analyse
    # - Spam-Signale: HIGH_CAPS, SPECIAL_CHARS, etc.
    return f"{sender} {sender} {sender} {domain} {domain} {domain} {caps_signal}{special_signal}{punct_signal}{url_signal}{keyword_signal}{subject} {body[:1000]}"
