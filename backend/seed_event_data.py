from datetime import datetime, timedelta, date
import random
from app.database import engine, SessionLocal
from app.models.social_media import TwitterPost, RedditPost
from app.models.events_topics import PoliticalEvent

def seed_event_data():
    db = SessionLocal()
    try:
        # Get the events we just created
        events = db.query(PoliticalEvent).all()
        if not events:
            print("No events found to seed data for.")
            return

        print(f"Found {len(events)} events. Seeding post data around their dates...")
        
        platforms = [("twitter", TwitterPost), ("reddit", RedditPost)]
        parties = ["BJP", "INC", "AAP", "SP", "TMC", "Unknown"]
        topics = [
            "This was a huge announcement! The budget allocations for infra are amazing.",
            "Really disappointed with the new policies. We expected more relief.",
            "The rally today saw a massive crowd. Strong support for the leadership.",
            "Election results are out and it's a shocking turn of events.",
            "Economy is recovering fast. Good steps by the gov.",
            "Inflation is still a major issue that needs to be addressed immediately."
        ]
        
        total_inserted = 0
        
        for event in events:
            event_dt = datetime.combine(event.date, datetime.min.time())
            
            # Generate random posts within +/- 7 days of the event
            for offset_days in range(-7, 8):
                current_dt = event_dt + timedelta(days=offset_days)
                
                # Create a burst of volume ON or right AFTER the event date
                volume_multiplier = random.randint(3, 8) if offset_days >= 0 and offset_days <= 2 else random.randint(1, 3)
                
                for i in range(volume_multiplier):
                    platform_name, Model = random.choice(platforms)
                    
                    # Generate a fake post
                    content = random.choice(topics)
                    sentiment_score = random.uniform(-0.8, 0.8) if offset_days < 0 else random.uniform(0.1, 0.9) # Shift sentiment positive after
                    
                    post = Model(
                        post_id=f"mock_{event.id}_{offset_days}_{i}_{platform_name}",
                        party=random.choice(parties),
                        username=f"user_{random.randint(1000, 9999)}",
                        source_type="public",
                        content=content,
                        language="en",
                        sentiment_label="positive" if sentiment_score > 0 else "negative",
                        sentiment_score=sentiment_score,
                        predicted_alignment=random.choice(parties),
                        alignment_confidence=random.uniform(0.5, 0.99),
                        likes=random.randint(0, 5000),
                        retweets=random.randint(0, 1000),
                        replies=random.randint(0, 500),
                        url=f"https://{platform_name}.com/post_{random.randint(1000, 9999)}",
                        posted_at=current_dt + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
                    )
                    db.add(post)
                    total_inserted += 1

        db.commit()
        print(f"Successfully seeded {total_inserted} mock posts around the events!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding post data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_event_data()
