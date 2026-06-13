import json
from pathlib import Path


MODEL_DIR = Path(__file__).resolve().parent / "saved_models"


def list_model_cards():
    cards = []
    if not MODEL_DIR.exists():
        return cards
    for card_path in sorted(MODEL_DIR.rglob("*.card.json")):
        try:
            with card_path.open("r", encoding="utf-8") as f:
                card = json.load(f)
            card["path"] = str(card_path.relative_to(MODEL_DIR))
            cards.append(card)
        except (OSError, json.JSONDecodeError):
            cards.append({"path": str(card_path.relative_to(MODEL_DIR)), "error": "unreadable model card"})
    return cards


def list_artifacts():
    if not MODEL_DIR.exists():
        return []
    return [
        str(path.relative_to(MODEL_DIR))
        for path in sorted(MODEL_DIR.rglob("*"))
        if path.is_file() and path.suffix in {".pkl", ".pt", ".json"}
    ]
