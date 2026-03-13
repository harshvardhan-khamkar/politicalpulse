import re
import pandas as pd
from typing import List

def clean_text(text: str) -> str:
    """
    Cleans social media text by removing URLs, mentions, and keeping only alphanumeric and basic punctuation.
    """
    if not isinstance(text, str):
        return ""
    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)
    # Remove user mentions
    text = re.sub(r'@\w+', '', text)
    # Remove non-alphanumeric characters but keep basic punctuation
    text = re.sub(r'[^a-zA-Z0-9\s#.,!?]', '', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()

def preprocess_dataframe(df: pd.DataFrame, text_column: str = 'text') -> pd.DataFrame:
    """
    Applies cleaning and filters out empty texts.
    """
    df['clean_text'] = df[text_column].apply(clean_text)
    # Drop rows with minimal text remaining (e.g., just an emoji or link originally)
    return df[df['clean_text'].str.len() > 10].copy()
