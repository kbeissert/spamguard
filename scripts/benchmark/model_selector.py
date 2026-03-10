import sys

import questionary
import requests

OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"


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


if __name__ == "__main__":
    # If run directly, print the selected model to stdout so it can be used in shell scripts
    # e.g. MODEL=$(python model_selector.py)
    model = select_model()
    if model:
        print(model)
