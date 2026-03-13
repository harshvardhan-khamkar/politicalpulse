import logging
import pickle
from typing import List, Any
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report

logger = logging.getLogger(__name__)

class AlignmentClassifier:
    """
    Supervised Machine Learning model for classifying political ideology / party alignment.
    Uses TF-IDF + Random Forest as a highly interpretable and robust baseline.
    """
    
    def __init__(self, max_features: int = 5000):
        self.vectorizer = TfidfVectorizer(max_features=max_features, ngram_range=(1, 2))
        self.classifier = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        self.is_trained = False

    def train(self, texts: List[str], labels: List[str], test_size: float = 0.2):
        """
        Trains the classifier and logs evaluation metrics.
        """
        logger.info(f"Training Alignment Classifier on {len(texts)} samples...")
        X = self.vectorizer.fit_transform(texts)
        
        X_train, X_test, y_train, y_test = train_test_split(X, labels, test_size=test_size, random_state=42)
        
        self.classifier.fit(X_train, y_train)
        self.is_trained = True
        
        y_pred = self.classifier.predict(X_test)
        report = classification_report(y_test, y_pred)
        logger.info("\n--- Alignment Model Evaluation Metrics ---")
        logger.info("\n" + report)
        
        return report

    def predict(self, texts: List[str]) -> List[str]:
        """
        Predicts alignment labels for new texts.
        """
        if not self.is_trained:
            raise ValueError("Model is not trained yet. Call train() first.")
            
        X = self.vectorizer.transform(texts)
        return self.classifier.predict(X).tolist()

    def predict_proba(self, texts: List[str]) -> List[dict]:
        """
        Returns prediction probabilities for all classes.
        """
        if not self.is_trained:
            raise ValueError("Model is not trained yet. Call train() first.")
            
        X = self.vectorizer.transform(texts)
        probs_array = self.classifier.predict_proba(X)
        classes = self.classifier.classes_
        
        results = []
        for probs in probs_array:
            prob_dict = {cls: prob for cls, prob in zip(classes, probs)}
            results.append(prob_dict)
            
        return results

    def save(self, path: str):
        """Saves vectorizer and model."""
        with open(path, 'wb') as f:
            pickle.dump({'vectorizer': self.vectorizer, 'model': self.classifier}, f)
            
    def load(self, path: str):
        """Loads vectorizer and model."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.vectorizer = data['vectorizer']
            self.classifier = data['model']
            self.is_trained = True
