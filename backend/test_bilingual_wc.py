import sys
import os

# Set path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.services.wordcloud_service import wordcloud_service

def test_bilingual_wordclouds():
    print("--- Testing Bilingual Word Clouds ---")
    db = SessionLocal()
    
    try:
        # Try to generate an english wordcloud for BJP (or any party)
        print("Generating EN wordcloud for party: BJP")
        img_bytes_en = wordcloud_service.generate_wordcloud(
            db, party="BJP", platform="twitter", days=365, language="en"
        )
        print(f"EN Wordcloud generated: {len(img_bytes_en)} bytes")
        
        # Try to generate a hindi wordcloud for BJP
        print("Generating HI wordcloud for party: BJP")
        img_bytes_hi = wordcloud_service.generate_wordcloud(
            db, party="BJP", platform="twitter", days=365, language="hi"
        )
        print(f"HI Wordcloud generated: {len(img_bytes_hi)} bytes")
        
        if len(img_bytes_en) > 1000 and len(img_bytes_hi) > 1000:
            print("SUCCESS: Both images properly generated.")
        else:
            print("WARNING: One or both images might be empty or missing data.")
            
    except Exception as e:
        print(f"Error generating wordcloud: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_bilingual_wordclouds()
