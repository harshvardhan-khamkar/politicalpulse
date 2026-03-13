import sys
import os
import io
from wordcloud import WordCloud

# Set path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.services.wordcloud_service import wordcloud_service

wordcloud_service._init_nltk()

text = "ममता बनर्जी और सरकार की जनता अपना काम कर रही है"
cleaned = wordcloud_service.clean_text(text)
print(f"Cleaned Text: [{cleaned}]")

# Test how the SERVICE would tokenize it
regexp = r"[\u0900-\u097F\u200C\u200D\w']+"
wc = WordCloud(regexp=regexp)
word_counts = wc.process_text(cleaned)
print("Service Tokenized counts:", word_counts)

# Apply our filter logic
filtered_counts = {w: freq for w, freq in word_counts.items() if len(w) > 1}
print("Filtered counts (Len > 1):", filtered_counts)

if any(len(w) == 1 for w in filtered_counts):
    print("FAILED: Single characters still present!")
else:
    print("SUCCESS: No single characters.")
