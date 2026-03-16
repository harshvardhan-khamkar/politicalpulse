import logging
import os
from typing import List, Dict
from pathlib import Path

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

    @property
    def _cache_dir(self) -> Path:
        return Path(__file__).resolve().parents[2] / ".hf_cache"

    def _initialize(self):
        try:
            from transformers import (
                AutoModelForSequenceClassification,
                AutoTokenizer,
                pipeline,
            )

            os.environ.setdefault("DISABLE_SAFETENSORS_CONVERSION", "1")
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            # Use GPU if available
            device = 0 if torch.cuda.is_available() else -1

            tokenizer = None
            model = None

            try:
                tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name,
                    cache_dir=str(self._cache_dir),
                    local_files_only=True,
                )
                model = AutoModelForSequenceClassification.from_pretrained(
                    self.model_name,
                    cache_dir=str(self._cache_dir),
                    local_files_only=True,
                    use_safetensors=False,
                )
                logger.info("Loaded cached sentiment model for offline inference")
            except Exception:
                logger.info("Cached sentiment model not found, downloading from Hugging Face")
                tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name,
                    cache_dir=str(self._cache_dir),
                )
                model = AutoModelForSequenceClassification.from_pretrained(
                    self.model_name,
                    cache_dir=str(self._cache_dir),
                    use_safetensors=False,
                )

            self.pipeline = pipeline(
                "sentiment-analysis",
                model=model,
                tokenizer=tokenizer,
                device=device,
            )
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
