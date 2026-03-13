import asyncio
from datetime import date, timedelta
from typing import Optional

from app.database import engine, SessionLocal
from app.models.events_topics import PoliticalEvent
from app.services.twitter_service import twitter_service

async def scrape_event_data(event_name: str, keyword: str, days: int = 7):
    db = SessionLocal()
    try:
        # 1. Scrape real tweets for the keyword
        print(f"Scraping Twitter for '{keyword}' over the last {days} days...")
        stats = await twitter_service.scrape_hashtag(
            db=db,
            hashtag=keyword,
            language="all",
            since_days=days,
            target_count=300,
            cooldown_seconds=(2, 4),
            product="Latest"
        )
        print(f"Scrape stats: {stats}")

        # 2. Insert the event so the dashboard maps it
        # We'll set the event date right in the middle of our scrape window
        event_date = date.today() - timedelta(days=(days // 2))
        
        # Check if an event with this name already exists
        existing_event = db.query(PoliticalEvent).filter(PoliticalEvent.name == event_name).first()
        if existing_event:
            print(f"Event '{event_name}' already exists.")
        else:
            print(f"Inserting new event '{event_name}' on {event_date}...")
            event = PoliticalEvent(
                name=event_name,
                description=f"Automated event inserted for term: {keyword}",
                date=event_date,
                keywords=keyword.lstrip('#'),
                impact_score=7.5
            )
            db.add(event)
            db.commit()
            print("Event inserted successfully.")
            
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Scrape data regarding the recent Maharashtra political shifts, or general Indian politics
    # Pick a broad keyword that guarantees hits across English and Hindi
    asyncio.run(scrape_event_data("Recent National Scrutiny", "#politics", days=4))
