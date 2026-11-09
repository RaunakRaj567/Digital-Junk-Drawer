"""
ml_classifier.py
Interfaces with the pre-trained Machine Learning model for document classification.

Loads 'file_classifier_model.pkl' (or 'model.pkl') created from the BBC news dataset,
cleans input file/folder names, and returns predicted categories:
- Business (or Buisness)
- Tech
- Politics
- Sports
- Entertainment
"""

import os
import re
from pathlib import Path
from typing import Tuple, Dict, Optional, Any
import warnings
import joblib

# Suppress minor scikit-learn version differences when loading pickled pipelines
warnings.filterwarnings("ignore", category=UserWarning)


# Canonical category title mapping
CATEGORY_TITLE_MAP = {
    "business": "Business",
    "buisness": "Business",
    "tech": "Tech",
    "politics": "Politics",
    "sport": "Sports",
    "sports": "Sports",
    "entertainment": "Entertainment"
}


def clean_filename_for_ml(name: str) -> str:
    """
    Preprocesses a file or folder name for classification:
    - Strips file extensions (e.g., .pdf, .docx, .mp4)
    - Splits camelCase / PascalCase ('PremierLeague' -> 'Premier League')
    - Replaces underscores, hyphens, and non-alphanumeric chars with spaces
    - Normalizes and lowercases tokens
    """
    base = os.path.basename(name.rstrip("/\\"))
    name_no_ext = os.path.splitext(base)[0]
    
    # Split camelCase / PascalCase
    s1 = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', name_no_ext)
    s2 = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', s1)
    
    # Remove symbols and punctuation
    clean = re.sub(r'[^a-zA-Z\s]', ' ', s2)
    return ' '.join(clean.lower().split())


class MLClassifier:
    """
    Wrapper for loading and executing predictions using the trained Naive Bayes
    text classification pipeline.
    """

    MODEL_PATHS = [
        "file_classifier_model.pkl",
        "model.pkl",
        os.path.join(os.path.dirname(__file__), "file_classifier_model.pkl"),
        os.path.join(os.path.dirname(__file__), "model.pkl")
    ]

    def __init__(self, model_path: Optional[str] = None):
        self.model: Optional[Any] = None
        self.model_path: Optional[str] = None
        self._load_model(model_path)

    def _load_model(self, model_path: Optional[str] = None) -> None:
        """Attempts to load the ML model from designated file paths."""
        paths_to_check = [model_path] if model_path else self.MODEL_PATHS

        for p in paths_to_check:
            if p and os.path.exists(p):
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        self.model = joblib.load(p)
                    self.model_path = p
                    return
                except Exception:
                    continue

        # If model file is not found, classifier will use heuristic fallback
        self.model = None

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def predict(self, filename_or_text: str) -> Tuple[str, float]:
        """
        Predicts the category of a document from its filename or text.

        Returns:
        --------
        Tuple[str, float] : (predicted_category_title, confidence_percentage)
        """
        cleaned_text = clean_filename_for_ml(filename_or_text)

        if not cleaned_text:
            return "Business", 50.0

        if self.model is not None:
            try:
                raw_pred = self.model.predict([cleaned_text])[0]
                probs = self.model.predict_proba([cleaned_text])[0]
                confidence = float(max(probs) * 100)
                category = CATEGORY_TITLE_MAP.get(str(raw_pred).lower(), str(raw_pred).capitalize())
                return category, round(confidence, 2)
            except Exception:
                pass

        # Intelligent heuristic fallback if model file is unavailable
        return self._heuristic_predict(cleaned_text)

    def _heuristic_predict(self, text: str) -> Tuple[str, float]:
        """Rule-based keyword fallback for testing or cold start environments."""
        keywords = {
            "Sports": ["football", "soccer", "cricket", "league", "match", "cup", "champion",
                       "nba", "goal", "player", "tennis", "tournament", "olympics", "race"],
            "Business": ["profit", "stock", "market", "revenue", "quarter", "earnings", "bank",
                         "investment", "shares", "inflation", "finance", "economy", "trade", "tax"],
            "Tech": ["ai", "software", "gpu", "apple", "iphone", "microsoft", "google", "cyber",
                     "malware", "hardware", "computer", "chip", "update", "app", "network", "code"],
            "Politics": ["election", "parliament", "minister", "president", "senate", "vote",
                         "government", "party", "policy", "campaign", "law", "debate", "mp"],
            "Entertainment": ["movie", "film", "oscar", "music", "song", "album", "actor",
                              "actress", "hollywood", "netflix", "award", "festival", "cinema", "star"]
        }
        
        scores = {cat: 0 for cat in keywords}
        tokens = text.lower().split()
        for token in tokens:
            for cat, words in keywords.items():
                if token in words:
                    scores[cat] += 1

        best_cat = max(scores, key=scores.get)
        if scores[best_cat] > 0:
            return best_cat, 85.0
        return "Business", 50.0  # Default fallback
