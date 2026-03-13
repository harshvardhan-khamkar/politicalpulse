import sys, os
from datetime import datetime
from sqlalchemy import func

# Append the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.social_media import TwitterPost
from app.models.events_topics import PoliticalEvent
from app.services.topic_modeling_service import topic_modeling_service

def auto_detect_real_events():
    db = SessionLocal()
    try:
        # Step 1: Clear existing dummy events
        db.query(PoliticalEvent).delete()
        db.commit()
        print("Cleared old dummy events.")

        # Step 2: Find the top 4 dates with the highest tweet volume
        daily_counts = db.query(
            func.date(TwitterPost.posted_at).label("d"), 
            func.count(TwitterPost.id).label("c")
        ).group_by("d").order_by(func.count(TwitterPost.id).desc()).limit(4).all()

        if not daily_counts:
            print("No tweets found in DB. Cannot detect events.")
            return

        print(f"Detected top {len(daily_counts)} peak days in tweet volume:")
        
        for d, count in daily_counts:
            # Step 3: Extract topics for that specific day to name the event
            posts = db.query(TwitterPost.content).filter(func.date(TwitterPost.posted_at) == d).all()
            texts = [p[0] for p in posts if p[0]]
            
            # Use topic modeling service to find what people were discussing
            topics = topic_modeling_service.extract_topics(texts, num_topics=1, top_n_words=4)
            
            if topics and topics[0]["keywords"]:
                keywords = topics[0]["keywords"]
                # Create a catchy name based on the top 2 keywords
                k1 = str(keywords[0]).capitalize()
                k2 = str(keywords[1]).capitalize()
                event_name = f"Surge in Discourse: {k1} & {k2}"
                keywords_str = ", ".join(keywords)
            else:
                event_name = f"Major Political Discussion Volume Spike"
                keywords_str = "politics, news, trending"

            # Step 4: Create the PoliticalEvent
            impact_score = min(10.0, max(5.0, count / 50.0)) # scale impact from 5 to 10
            
            new_event = PoliticalEvent(
                name=event_name,
                description=f"Auto-detected event matching a massive spike of {count} social media posts. Key topics driving this spike included: {keywords_str}.",
                date=d,
                keywords=keywords_str,
                impact_score=round(impact_score, 2)
            )
            db.add(new_event)
            print(f" -> Created Event '{event_name}' on {d} (Volume: {count})")

        db.commit()
        print("\nSuccessfully auto-generated real events based on tweet data!")

    except Exception as e:
        db.rollback()
        print(f"Error during auto-detection: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    auto_detect_real_events()
