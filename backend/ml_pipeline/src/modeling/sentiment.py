import logging
from typing import List, Dict
import torch

logger = logging.getLogger(__name__)

class TransformerSentimentAnalyzer:
    """
    Uses a highly accurate Transformer model (RoBERTa fine-tuned for Twitter/Social Media).
    Classifies text into Positive, Neutral, Negative.
    """
    
    def __init__(self, model_name: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"):
        self.model_name = model_name
        self.pipeline = None
        self._initialize()

    def _initialize(self):
        try:
            from transformers import pipeline
            # Use GPU if available
            device = 0 if torch.cuda.is_available() else -1
            self.pipeline = pipeline("sentiment-analysis", model=self.model_name, device=device)
            logger.info(f"Loaded Sentiment Transformer: {self.model_name}")
        except ImportError:
            logger.error("HuggingFace 'transformers' or 'torch' not installed. Install via requirements_ml.txt")
            raise

    def analyze_batch(self, texts: List[str]) -> List[Dict[str, any]]:
        """
        Runs sentiment analysis on a batch of strings.
        Output format: [{'label': 'positive', 'score': 0.98}, ...]
        """
        if not self.pipeline:
            return [{"label": "neutral", "score": 0.0}] * len(texts)
            
        # Transform max length to 512 (RoBERTa limit)
        results = self.pipeline(texts, truncation=True, max_length=512)
        return results
