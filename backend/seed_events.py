from datetime import date, timedelta
from app.database import engine, SessionLocal
from app.models.events_topics import PoliticalEvent

def seed_events():
    db = SessionLocal()
    try:
        # Create an event representing recent political activity
        recent_date = date.today() - timedelta(days=2)
        event1 = PoliticalEvent(
            name="Recent Major Rally / Announcement",
            description="A significant political event that occurred recently, driving major social media discussion.",
            date=recent_date,
            keywords="announcement, rally, speech",
            impact_score=8.5
        )
        
        # Another event a week ago
        past_date = date.today() - timedelta(days=10)
        event2 = PoliticalEvent(
            name="State Election Results",
            description="Results for recent assembly elections declared, shifting the political discourse.",
            date=past_date,
            keywords="election, results, win, lose",
            impact_score=9.0
        )
        
        db.add(event1)
        db.add(event2)
        db.commit()
        print("Events seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding events: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_events()
