"""
Alignment Model Service
Predicts the political alignment of a text using lightweight Logistic Regression.
Trains on known official political handles.
"""
import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class AlignmentModelService:
    """Classifies text into political leanings based on trained TF-IDF features."""
    
    def __init__(self):
        self.vectorizer = None
        self.classifier = None
        self.initialized = False
        self.label_encoder = None
        
    def _init_models(self):
        """Lazy load scikit-learn"""
        if self.initialized:
            return
            
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
            from sklearn.preprocessing import LabelEncoder
            
            self.vectorizer = TfidfVectorizer(
                lowercase=True,
                stop_words='english',
                max_features=2000,
                ngram_range=(1, 2)
            )
            
            # Logistic Regression is lightweight, fast, and works well with sparse text data
            self.classifier = LogisticRegression(class_weight='balanced', random_state=42, max_iter=1000)
            self.label_encoder = LabelEncoder()
            
            self.initialized = True
            logger.info("Alignment Model parameters initialized successfully")
        except ImportError:
            logger.error("scikit-learn not installed. Install with: pip install scikit-learn")
            self.initialized = False

    def train_model(self, db_session) -> Dict[str, Any]:
        """
        Train the model using data from the database where source_type='political'.
        Returns training metrics.
        """
        self._init_models()
        if not self.initialized:
            return {"error": "Dependencies missing"}
            
        from app.models.social_media import TwitterPost
        
        try:
            # Note: We can expand this to Reddit if we know party handles there
            # For now, train on political Twitter handles where party is known
            political_posts = db_session.query(TwitterPost)\
                .filter(TwitterPost.source_type == 'political')\
                .filter(TwitterPost.party.isnot(None))\
                .all()
                
            if len(political_posts) < 50:
                logger.warning("Insufficient training data for alignment classifier")
                return {"error": "Not enough political posts to train (Need at least 50)"}
                
            texts = [p.content for p in political_posts if p.content]
            labels = [p.party for p in political_posts if p.content]
            
            # Encode labels
            y = self.label_encoder.fit_transform(labels)
            
            # Vectorize text
            X = self.vectorizer.fit_transform(texts)
            
            # Train model
            self.classifier.fit(X, y)
            
            accuracy = self.classifier.score(X, y)
            
            logger.info(f"Alignment model trained on {len(texts)} samples. Classes: {self.label_encoder.classes_}")
            
            return {
                "status": "success",
                "samples_trained": len(texts),
                "classes": self.label_encoder.classes_.tolist(),
                "training_accuracy": round(accuracy, 4)
            }
            
        except Exception as e:
            logger.exception(f"Error training alignment model: {e}")
            return {"error": str(e)}
            
    def predict_alignment(self, text: str) -> Dict[str, Any]:
        """
        Predicts alignment for a given text.
        Requires the model to be trained first.
        """
        if not text or not self.initialized or not hasattr(self.classifier, 'classes_'):
            return {
                "predicted_alignment": "Unknown",
                "alignment_confidence": 0.0
            }
            
        try:
            X = self.vectorizer.transform([text])
            
            # Get probabilities
            probs = self.classifier.predict_proba(X)[0]
            
            # Get highest prob
            max_prob_idx = probs.argmax()
            confidence = probs[max_prob_idx]
            
            predicted_party = self.label_encoder.inverse_transform([max_prob_idx])[0]
            
            # Threshold to avoid classifying noise
            if confidence < 0.35:  # Low confidence threshold
                predicted_party = "Neutral/Unknown"
                
            return {
                "predicted_alignment": predicted_party,
                "alignment_confidence": round(float(confidence), 4)
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {
                "predicted_alignment": "Unknown",
                "alignment_confidence": 0.0
            }


# Global instance
alignment_model_service = AlignmentModelService()
