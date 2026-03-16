import logging
from typing import List, Tuple
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

class BERTopicModeler:
    """
    Advanced Topic Modeling using BERTopic (SentenceTransformers + HDBSCAN).
    Ideal for short social media posts.
    """
    
    def __init__(self):
        self.topic_model = None
        self._initialize()

    @property
    def _cache_dir(self) -> Path:
        return Path(__file__).resolve().parents[2] / ".hf_cache"

    def _initialize(self):
        try:
            from bertopic import BERTopic
            from sentence_transformers import SentenceTransformer

            self._cache_dir.mkdir(parents=True, exist_ok=True)
            embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"

            try:
                embedding_model = SentenceTransformer(
                    embedding_model_name,
                    cache_folder=str(self._cache_dir),
                    local_files_only=True,
                )
                logger.info("Loaded cached sentence-transformer for BERTopic")
            except Exception:
                logger.info("Cached BERTopic embedding model not found, downloading from Hugging Face")
                embedding_model = SentenceTransformer(
                    embedding_model_name,
                    cache_folder=str(self._cache_dir),
                )

            # Calculate probabilities slows down training significantly, skip if not needed
            self.topic_model = BERTopic(
                language="english",
                embedding_model=embedding_model,
                calculate_probabilities=False,
                verbose=True,
            )
            logger.info("BERTopic initialized successfully")
        except ImportError:
            logger.error("'bertopic' not installed. Install via requirements_ml.txt")
            raise

    def fit_transform(self, docs: List[str]) -> Tuple[List[int], pd.DataFrame]:
        """
        Fits the topic model on documents and returns assigned topics and a summary DataFrame.
        """
        if not docs or len(docs) < 50:
            logger.warning("BERTopic requires a sufficient number of documents (preferably > 50).")
            return [], pd.DataFrame()
            
        topics, probs = self.topic_model.fit_transform(docs)
        
        # Get the DataFrame containing topic representations
        topic_info = self.topic_model.get_topic_info()
        return topics, topic_info

    def get_topic_keywords(self, topic_id: int) -> List[str]:
        """Returns the top keywords for a specific topic."""
        if not self.topic_model:
            return []
        
        # Returns list of tuples (Word, Score)
        topic_words = self.topic_model.get_topic(topic_id)
        if topic_words:
            return [word for word, score in topic_words]
        return []
        
    def save_model(self, path: str):
        if self.topic_model:
            self.topic_model.save(path)
