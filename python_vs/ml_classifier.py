"""
ml_classifier.py - Machine Learning Classifier for Engineering Drawing Annotations
Project: Automation of Quality Inspection Report Generation
Client: MJMTECHNOVA ENGINEERING PVT. LTD.
Academic Mentorship: Prof. Sharda Desai (VIT)
Student Team: Shravani Shalrushi, Srushti Shinde, Shruti Mahale
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import pickle
import pandas as pd
import numpy as np

from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset" / "training_data.csv"
MODEL_PATH = BASE_DIR / "dataset" / "drawing_text_classifier.pkl"
METRICS_PATH = BASE_DIR / "dataset" / "model_evaluation.txt"


def train_and_evaluate_classifier():
    """
    Trains a high-performance NLP classifier on drawing text annotations.
    Evaluates with Stratified K-Fold and persists the trained model.
    """
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}. Run prepare_dataset.py first.")

    df = pd.read_csv(DATASET_PATH, encoding="utf-8-sig")
    print(f"Loaded {len(df)} samples from {DATASET_PATH.name}")

    X = df["text"].astype(str)
    y = df["category"].astype(str)

    # Hybrid TF-IDF on character n-grams and word tokens
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 3),
            analyzer="char_wb",
            lowercase=True,
            min_df=1
        )),
        ("clf", LogisticRegression(
            C=10.0,
            max_iter=1000,
            class_weight="balanced",
            random_state=42
        ))
    ])

    # 5-Fold Stratified Cross-Validation
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(pipeline, X, y, cv=skf, scoring="accuracy")

    print("\n--- Model Evaluation (5-Fold Stratified Cross-Validation) ---")
    print(f"Fold Accuracies: {[round(s, 4) for s in scores]}")
    print(f"Mean Accuracy: {scores.mean() * 100:.2f}% (± {scores.std() * 100:.2f}%)")

    # Train on full dataset
    pipeline.fit(X, y)

    # Generate full report
    preds = pipeline.predict(X)
    report_str = classification_report(y, preds, zero_division=0)
    print("\nClassification Report (Full Training Set):")
    print(report_str)

    # Save evaluation summary
    eval_text = (
        f"MJMTECHNOVA QUALITY INSPECTION AI CLASSIFIER EVALUATION\n"
        f"Model: TF-IDF Char-WB + Balanced Logistic Regression\n"
        f"----------------------------------------------------\n"
        f"5-Fold CV Mean Accuracy: {scores.mean() * 100:.2f}% (± {scores.std() * 100:.2f}%)\n\n"
        f"Full Classification Report:\n{report_str}\n"
    )
    METRICS_PATH.write_text(eval_text, encoding="utf-8")
    print(f"Saved evaluation metrics to: {METRICS_PATH}")

    # Persist model
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f)
    print(f"Trained model saved to: {MODEL_PATH}")

    return pipeline


class DrawingAnnotationClassifier:
    """Inference helper for predicting labels of new drawing text."""

    def __init__(self, model_file: Path = MODEL_PATH):
        if not model_file.exists():
            print(f"Model file {model_file} not found. Training new model...")
            self.model = train_and_evaluate_classifier()
        else:
            with open(model_file, "rb") as f:
                self.model = pickle.load(f)

    def predict(self, text: str) -> dict:
        """Predicts category and probability for an annotation string."""
        clean_text = str(text).strip()
        category = self.model.predict([clean_text])[0]
        probs = self.model.predict_proba([clean_text])[0]
        classes = self.model.classes_
        confidence = float(np.max(probs))

        return {
            "text": clean_text,
            "predicted_category": category,
            "confidence": round(confidence, 4),
            "top_probabilities": {cls: round(float(p), 4) for cls, p in zip(classes, probs) if p > 0.05}
        }


def main():
    train_and_evaluate_classifier()

    # Test inference on test snippets
    clf = DrawingAnnotationClassifier()
    test_cases = [
        "M5 - 6H ↧ 10",
        "4X Ø3.4 THRU",
        "16±0.02",
        "204.5 mm",
        "0.5 x 45°",
        "R 3 TYP",
        "A.1 X=132.5mm",
        "⌖ 0.05 A"
    ]
    print("\n--- Test Predictions on Engineering Callouts ---")
    for t in test_cases:
        res = clf.predict(t)
        print(f"'{t}' => {res['predicted_category']} (Conf: {res['confidence'] * 100:.1f}%)")


if __name__ == "__main__":
    main()
