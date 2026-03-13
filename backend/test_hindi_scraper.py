import asyncio
import sys
import os

# Set path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.services.twitter_service import twitter_service

async def test_scraper():
    db = SessionLocal()
    print("Initializing client...")
    twitter_service._init_client()
    
    print("Testing Hindi scraper with BJP...")
    try:
        results = await twitter_service.scrape_party_tweets(
            db, party="BJP", language="hi", since_days=7, include_public=True, target_count=5
        )
        print("Hindi Scraper results:", results)
        
        # Test just the query builder
        queries = []
        queries.extend(twitter_service._build_handles_query(["BJP4India"], "hi", 7))
        queries.extend(twitter_service._build_public_query(["#BJP"], "hi", 7))
        print("Queries built:", queries)
        
    except Exception as e:
        print("Failed:", e)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_scraper())
