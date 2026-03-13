"""
Event Correlation Service
Analyzes discourse shifts around major political events.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy import func

from app.services.topic_modeling_service import topic_modeling_service

logger = logging.getLogger(__name__)

class EventCorrelationService:
    """Provides analytics on how social discourse changes before and after events."""
    
    def analyze_event_impact(self, db_session, event_id: int, window_days: int = 7) -> Dict[str, Any]:
        """
        Compare sentiment and engagement N days before vs N days after an event.
        """
        from app.models.events_topics import PoliticalEvent
        from app.models.social_media import TwitterPost, RedditPost
        
        event = db_session.query(PoliticalEvent).filter(PoliticalEvent.id == event_id).first()
        if not event:
            return {"error": "Event not found"}
            
        # Define time windows
        event_date = datetime.combine(event.date, datetime.min.time())
        pre_start = event_date - timedelta(days=window_days)
        post_end = event_date + timedelta(days=window_days)
        
        # Helper to get stats for a window
        def get_window_stats(model, start_dt, end_dt):
            stats = db_session.query(
                func.count(model.id).label("volume"),
                func.avg(model.sentiment_score).label("avg_sentiment")
            ).filter(model.posted_at >= start_dt, model.posted_at < end_dt).first()
            
            return {
                "volume": stats.volume or 0,
                "avg_sentiment": float(stats.avg_sentiment) if stats.avg_sentiment else 0.0
            }
            
        # Get stats for Twitter
        twitter_pre = get_window_stats(TwitterPost, pre_start, event_date)
        twitter_post = get_window_stats(TwitterPost, event_date, post_end)
        
        # Get stats for Reddit
        reddit_pre = get_window_stats(RedditPost, pre_start, event_date)
        reddit_post = get_window_stats(RedditPost, event_date, post_end)
        
        # Calculate shifts
        def calc_shift(pre, post):
            vol_shift = post['volume'] - pre['volume']
            vol_pct = (vol_shift / pre['volume'] * 100) if pre['volume'] > 0 else 0
            
            sentiment_shift = post['avg_sentiment'] - pre['avg_sentiment']
            
            return {
                "volume_change": vol_shift,
                "volume_pct_change": round(vol_pct, 2),
                "sentiment_change": round(sentiment_shift, 4)
            }
            
        twitter_shift = calc_shift(twitter_pre, twitter_post)
        reddit_shift = calc_shift(reddit_pre, reddit_post)
        
        # Helper to extract topics for a given pool of posts
        def get_topic_sentiment(start_dt, end_dt) -> List[Dict]:
            # Fetch raw text from both platforms
            tw_posts = db_session.query(TwitterPost.content, TwitterPost.sentiment_score).filter(
                TwitterPost.posted_at >= start_dt, TwitterPost.posted_at < end_dt
            ).all()
            rd_posts = db_session.query(RedditPost.content, RedditPost.sentiment_score).filter(
                RedditPost.posted_at >= start_dt, RedditPost.posted_at < end_dt
            ).all()
            
            all_posts = tw_posts + rd_posts
            if not all_posts:
                return []
                
            texts = [p[0] for p in all_posts if p[0]]
            
            # Use the NMF model to find 3 main topics per window
            topics = topic_modeling_service.extract_topics(texts, num_topics=3, top_n_words=5)
            
            # Approximate sentiment per topic by checking if keywords appear in post
            # (A rough but fast way without aspect-based sentiment routing)
            for t in topics:
                keywords = set(t["keywords"])
                topic_sentiments = []
                for content, score in all_posts:
                    if content and score is not None:
                        # If post contains topic keywords
                        content_lower = content.lower()
                        if any(kw in content_lower for kw in keywords):
                            topic_sentiments.append(float(score))
                
                if topic_sentiments:
                    avg_s = sum(topic_sentiments) / len(topic_sentiments)
                else:
                    avg_s = 0.0
                t["average_sentiment"] = round(avg_s, 4)
                
            return topics

        # Simple heuristic: heavily weighting volume spikes and sentiment swings
        total_vol_shift = twitter_shift["volume_change"] + reddit_shift["volume_change"]
        abs_sentiment_shift = abs(twitter_shift["sentiment_change"]) + abs(reddit_shift["sentiment_change"])
        calculated_impact = min(10.0, (abs(total_vol_shift) / 1000.0) + (abs_sentiment_shift * 5))
        
        pre_topics = get_topic_sentiment(pre_start, event_date)
        post_topics = get_topic_sentiment(event_date, post_end)
        
        return {
            "event_id": event.id,
            "event_name": event.name,
            "event_date": event.date,
            "window_days": window_days,
            "pre_event": {
                "twitter": twitter_pre,
                "reddit": reddit_pre,
                "topics": pre_topics
            },
            "post_event": {
                "twitter": twitter_post,
                "reddit": reddit_post,
                "topics": post_topics
            },
            "shifts": {
                "twitter": twitter_shift,
                "reddit": reddit_shift
            },
            "calculated_impact_score": round(calculated_impact, 2)
        }

# Global instance
event_correlation_service = EventCorrelationService()
