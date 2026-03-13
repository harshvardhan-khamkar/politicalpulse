"""
Topic Modeling Service
Uses lightweight TF-IDF & NMF to extract topics from social texts.
"""
import logging
import re
from typing import List, Dict, Any, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class TopicModelingService:
    """Extracts thematic topics from a corpus of texts using TF-IDF + NMF."""
    
    def __init__(self):
        self.vectorizer = None
        self.nmf_model = None
        self.initialized = False
        
        # Stop words: basic English + Indian political context
        self.stop_words = set([
            # General English
            'the', 'is', 'in', 'and', 'to', 'of', 'for', 'it', 'on', 'with', 'a', 'an', 'at',
            'this', 'that', 'by', 'from', 'but', 'not', 'are', 'was', 'as', 'be', 'have',
            'has', 'had', 'will', 'or', 'if', 'they', 'their', 'which', 'who', 'what',
            'you', 'your', 'i', 'my', 'me', 'we', 'our', 'us', 'he', 'his', 'him', 'she', 'her',
            'do', 'does', 'did', 'so', 'can', 'could', 'would', 'should',
            
            # Political / Contextual noise
            'rt', 'http', 'https', 'amp', 'co', 'com', 'www', 'via', 'sir', 'madam', 'pls',
            'please', 'ji', 'shri', 'smt', 'dr', 'mr', 'mrs', 'today', 'tomorrow', 'yesterday',
            'people', 'country', 'india', 'indian', 'nation', 'state', 'government', 'govt'
        ])
    
    def _init_models(self):
        """Lazy load scikit-learn"""
        if self.initialized:
            return
            
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.decomposition import NMF
            
            def custom_tokenizer(text):
                # Lowercase, remove non-alphanumeric, split by space
                text = text.lower()
                text = re.sub(r'http\S+', '', text) # remove urls
                text = re.sub(r'[^a-z\s]', ' ', text) # keep only English letters for topic modeling
                tokens = text.split()
                return [t for t in tokens if len(t) > 2 and t not in self.stop_words]

            self.vectorizer = TfidfVectorizer(
                tokenizer=custom_tokenizer,
                max_df=0.95,       # ignore terms appearing in >95% of documents
                min_df=2,          # ignore terms appearing in <2 documents
                max_features=1000  # keep top 1000 terms
            )
            
            # Using NMF (Non-negative Matrix Factorization) as it often yields more interpretable 
            # topics for short text compared to LDA in scikit-learn.
            self.nmf_model = NMF(
                n_components=5,    # Extract top 5 topics by default
                random_state=42,
                init='nndsvd'      # Better initialization for NMF
            )
            
            self.initialized = True
            logger.info("Topic Modeling (TF-IDF + NMF) initialized successfully")
        except ImportError:
            logger.error("scikit-learn not installed. Install with: pip install scikit-learn")
            self.initialized = False
            
    def extract_topics(self, texts: List[str], num_topics: int = 5, top_n_words: int = 7) -> List[Dict[str, Any]]:
        """
        Extract topics from a list of texts.
        
        Returns:
            List of dictionaries containing topic keywords and prominence/salience score.
        """
        if not texts or len(texts) < 10:
            logger.warning("Not enough texts for meaningful topic modeling (need >= 10)")
            return []
            
        self._init_models()
        if not self.initialized:
            return []
            
        try:
            # Update n_components if different
            if self.nmf_model.n_components != num_topics:
                from sklearn.decomposition import NMF
                self.nmf_model = NMF(n_components=num_topics, random_state=42, init='nndsvd')
                
            # Document-Term Matrix
            dtm = self.vectorizer.fit_transform(texts)
            
            # Document-Topic Matrix
            W = self.nmf_model.fit_transform(dtm)
            
            # Topic-Term Matrix
            H = self.nmf_model.components_
            
            # Feature names mapping
            feature_names = self.vectorizer.get_feature_names_out()
            
            topics = []
            
            # Calculate total weight (salience) for each topic across all documents
            topic_weights = W.sum(axis=0)
            total_weight = topic_weights.sum() if topic_weights.sum() > 0 else 1.0
            
            for topic_idx, topic_row in enumerate(H):
                # Get indices of top words
                top_word_indices = topic_row.argsort()[:-top_n_words - 1:-1]
                keywords = [feature_names[i] for i in top_word_indices]
                
                # Salience as percentage of total weight
                salience = float(topic_weights[topic_idx] / total_weight)
                
                # Assign a generic name based on top 2 keywords
                topic_name = f"{keywords[0].capitalize()}-{keywords[1].capitalize()}" if len(keywords) >= 2 else f"Topic {topic_idx+1}"
                
                topics.append({
                    "topic_name": topic_name,
                    "keywords": keywords,
                    "salience_score": round(salience, 4)
                })
                
            # Sort by salience
            topics.sort(key=lambda x: x["salience_score"], reverse=True)
            return topics
            
        except Exception as e:
            logger.exception(f"Error during topic extraction: {e}")
            return []

# Global instance
topic_modeling_service = TopicModelingService()
