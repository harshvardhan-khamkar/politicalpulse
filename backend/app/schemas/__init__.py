# Schemas package - import all schemas
from app.schemas.elections import (
    ElectionResultBase,
    ElectionResultQuery,
    ElectionResultResponse
)
from app.schemas.polls import (
    PollTypeEnum,
    PollOption,
    PollCreate,
    PollUpdate,
    PollResponse,
    VoteCreate,
    VoteResponse,
    PollResults
)
from app.schemas.parties import (
    PartyBase,
    PartyCreate,
    PartyUpdate,
    PartyResponse,
    PartyListResponse,
    PartyLeaderBase,
    PartyLeaderCreate,
    PartyLeaderUpdate,
    PartyLeaderResponse
)
from app.schemas.social_media import (
    SocialPostBase,
    SocialPostCreate,
    SocialPostResponse,
    SentimentDataCreate,
    SentimentDataResponse,
    SentimentQuery
)
from app.schemas.predictions_news import (
    PredictionCreate,
    PredictionResponse,
    NewsArticleCreate,
    NewsArticleResponse,
    NewsQuery,
    CachedNewsArticle,
    CachedNewsResponse,
)

__all__ = [
    # Elections
    "ElectionResultBase",
    "ElectionResultQuery",
    "ElectionResultResponse",
    # Polls
    "PollTypeEnum",
    "PollOption",
    "PollCreate",
    "PollUpdate",
    "PollResponse",
    "VoteCreate",
    "VoteResponse",
    "PollResults",
    # Parties
    "PartyBase",
    "PartyCreate",
    "PartyUpdate",
    "PartyResponse",
    "PartyListResponse",
    "PartyLeaderBase",
    "PartyLeaderCreate",
    "PartyLeaderUpdate",
    "PartyLeaderResponse",
    # Social Media
    "SocialPostBase",
    "SocialPostCreate",
    "SocialPostResponse",
    "SentimentDataCreate",
    "SentimentDataResponse",
    "SentimentQuery",
    # Predictions & News
    "PredictionCreate",
    "PredictionResponse",
    "NewsArticleCreate",
    "NewsArticleResponse",
    "NewsQuery",
    "CachedNewsArticle",
    "CachedNewsResponse",
]
