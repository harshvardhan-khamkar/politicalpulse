# Import all models here for Alembic to detect them
from app.models.elections import ElectionResult
from app.models.social_media import TwitterPost, RedditPost, SentimentData
from app.models.polls import Poll, PollVote
from app.models.parties import Party, PartyLeader
from app.models.predictions_news import Prediction, NewsArticle
from app.models.users import AppUser
from app.models.events_topics import PoliticalEvent, TopicData

__all__ = [
    "ElectionResult",
    "TwitterPost",
    "RedditPost",
    "SentimentData",
    "Poll",
    "PollVote",
    "Party",
    "PartyLeader",
    "Prediction",
    "NewsArticle",
    "AppUser",
    "PoliticalEvent",
    "TopicData",
]
