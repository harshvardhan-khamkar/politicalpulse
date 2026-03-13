import pandas as pd
import logging
from src.preprocess.cleaner import preprocess_dataframe
from src.modeling.sentiment import TransformerSentimentAnalyzer
from src.modeling.topics import BERTopicModeler
from src.modeling.alignment import AlignmentClassifier

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PoliticalDiscoursePipeline:
    def __init__(self):
        logger.info("Initializing Political Discourse Pipeline...")
        self.sentiment_model = TransformerSentimentAnalyzer()
        self.topic_model = BERTopicModeler()
        self.alignment_model = AlignmentClassifier()

    def run_inference_pipeline(self, df: pd.DataFrame, text_column: str = 'text') -> pd.DataFrame:
        """
        Orchestrates sentiment, topics, and alignment extraction over a pandas DataFrame.
        """
        logger.info(f"Started pipeline on {len(df)} rows.")
        
        # 1. Preprocess
        logger.info("1. Preprocessing and cleaning text...")
        df = preprocess_dataframe(df, text_column)
        
        if df.empty:
            logger.warning("No valid text remaining after preprocessing.")
            return df
            
        texts = df['clean_text'].tolist()
        
        # 2. Add Sentiment
        logger.info("2. Analyzing Sentiment using Transformer...")
        sentiment_results = self.sentiment_model.analyze_batch(texts)
        df['sentiment_label'] = [res['label'] for res in sentiment_results]
        df['sentiment_score'] = [res['score'] for res in sentiment_results]
        
        # 3. Add Topics
        logger.info("3. Extracting Topics using BERTopic...")
        try:
            topics, _ = self.topic_model.fit_transform(texts)
            df['topic_id'] = topics
        except Exception as e:
            logger.warning(f"Could not fit topics (likely too few docs). Error: {e}")
            df['topic_id'] = -1
            
        # 4. Add Alignment Prediction (if trained)
        logger.info("4. Inferring Political Alignment...")
        if self.alignment_model.is_trained:
            try:
                alignments = self.alignment_model.predict(texts)
                df['predicted_alignment'] = alignments
            except Exception as e:
                logger.error(f"Error predicting alignment: {e}")
                df['predicted_alignment'] = 'Unknown'
        else:
            logger.warning("Alignment model is not trained. Skipping inference. Call pipeline.alignment_model.train() first.")
            df['predicted_alignment'] = 'Untrained'
            
        logger.info("Pipeline execution complete.")
        return df

if __name__ == "__main__":
    # Sample Mock Run
    import pandas as pd
    
    mock_data = pd.DataFrame({
        'post_id': [1, 2, 3, 4],
        'text': [
            "The infrastructure reform bill will save the middle class. #Progress",
            "This tax cut only benefits the billionaire elite corporations.",
            "I support the new healthcare initiatives. Universal coverage is vital.",
            "Regulations are destroying local businesses and killing jobs."
        ]
    })
    
    pipeline = PoliticalDiscoursePipeline()
    result_df = pipeline.run_inference_pipeline(mock_data)
    
    print("\nResulting Dataframe Head:")
    print(result_df[['clean_text', 'sentiment_label', 'topic_id', 'predicted_alignment']])
