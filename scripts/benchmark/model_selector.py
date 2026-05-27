import sys

import questionary
import requests

OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"

# Embedding-Modelle sind keine Chat-Modelle — für Benchmark ausschließen
_EMBED_KEYWORDS = ("embed", "embedding", "bge-", "nomic-embed", "mxbai-embed")


def get_ollama_models() -> list[str]:
    """Fetches the list of available models from Ollama."""
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        models = [model["name"] for model in data.get("models", [])]
        return sorted(models)
    except Exception as e:
        print(f"Warning: Could not fetch models from Ollama: {e}", file=sys.stderr)
        return []


def get_chat_models() -> list[str]:
    """Wie get_ollama_models(), aber ohne Embedding-Modelle."""
    return [
        m for m in get_ollama_models()
        if not any(kw in m.lower() for kw in _EMBED_KEYWORDS)
    ]


def select_model() -> str:
    """Interactively selects a model from the available Ollama models."""
    print("Fetching available models from Ollama...")
    available_models = get_ollama_models()

    if not available_models:
        print("⚠️  No models found in Ollama or connection failed.")
        print(
            "   Please ensure Ollama is running (ollama serve) and you have pulled models."
        )
        return None

    # Interactive selection
    return questionary.select(
        "Select the model you want to use:", choices=available_models
    ).ask()


def select_models() -> list[str]:
    """Wählt ein oder mehrere Modelle aus. Gibt Liste zurück.

    Erste Option: "Alle Modelle (Batch)" → liefert alle Chat-Modelle.
    Sonst: einzelnes Modell → liefert einelementige Liste.
    """
    print("Lade verfügbare Modelle aus Ollama...")
    available = get_chat_models()

    if not available:
        print("⚠️  Keine Modelle in Ollama gefunden.")
        print("   Stelle sicher dass Ollama läuft: ollama serve")
        return []

    _ALL = f"[ Alle Modelle — Batch-Benchmark ({len(available)} Modelle) ]"
    choices = [_ALL, questionary.Separator("─" * 40)] + available

    selection = questionary.select(
        "Modell für Real-Benchmark auswählen:",
        choices=choices,
    ).ask()

    if selection is None:
        return []
    if selection == _ALL:
        print(f"   → Batch-Modus: {len(available)} Modelle werden nacheinander getestet")
        return available
    return [selection]


if __name__ == "__main__":
    # If run directly, print the selected model to stdout so it can be used in shell scripts
    # e.g. MODEL=$(python model_selector.py)
    model = select_model()
    if model:
        print(model)
