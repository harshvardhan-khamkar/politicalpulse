import sys
import os

# Set path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.services.wordcloud_service import wordcloud_service

wordcloud_service._init_nltk()

tests = [
	"Today we are working on the state every year",  # Should be mostly empty
	"ममता बनर्जी आज सरकार के साथ है",               # Should filter 'आज', 'के', 'साथ', 'है'
	"Rahul Gandhi says Bengal needs vision",
	"Narendra Modi talks about economic growth"
]

print("Original -> Cleaned (Ideology Focus)")
for t in tests:
	cleaned = wordcloud_service.clean_text(t)
	print(f"[{t}] -> [{cleaned}]")
