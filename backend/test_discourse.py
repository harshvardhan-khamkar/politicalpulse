import sys, os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.database import SessionLocal
from app.services.event_correlation_service import event_correlation_service

try:
    db = SessionLocal()
    # Try fetching first event id for test
    from app.models.events_topics import PoliticalEvent
    event = db.query(PoliticalEvent).first()
    if event:
        print(f"Testing with event ID {event.id}: {event.name}")
        res = event_correlation_service.analyze_event_impact(db, event.id, 7)
        print("SUCCESS:", res)
    else:
        print("No events found in DB to test. But script loaded fine.")
except Exception as e:
    import traceback
    traceback.print_exc()
