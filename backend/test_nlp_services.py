import sys
import os

# Set path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.sentiment_service import sentiment_analyzer
from app.services.wordcloud_service import wordcloud_service

def test_sentiment():
    print("--- Testing Sentiment Service ---")
    texts = [
        "This government policy is absolutely fantastic! Best decision ever.",
        "Worst corruption scam in history. They should be ashamed.",
        "The new bridge construction is starting tomorrow.",
        "bura ganda harana bhrasht sarkar", # Hindi in English script
        "यह सरकार बहुत अच्छी है। मुझे इन पर गर्व है।" # Pure Hindi (Positive)
    ]
    
    for t in texts:
        result = sentiment_analyzer.analyze_sentiment(t)
        print(f"Text: {t}")
        print(f"Result: {result}\n")

def test_wordcloud():
    print("--- Testing NLTK Init ---")
    try:
        wordcloud_service._init_nltk()
        print("NLTK Init Successful - Stopwords & Lemmatizer loaded.")
        print(f"Number of stopwords: {len(wordcloud_service.stopwords)}")
    except Exception as e:
        print(f"Failed to init NLTK: {e}")

if __name__ == "__main__":
    test_sentiment()
    test_wordcloud()
