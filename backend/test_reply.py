import asyncio
from app.database import SessionLocal
from app.models.social_media import TwitterPost
from app.services.twitter_service import twitter_service

async def test():
    await twitter_service._initialize_client(force_relogin=True)
    
    db = SessionLocal()
    post = db.query(TwitterPost).filter(TwitterPost.replies > 5).order_by(TwitterPost.replies.desc()).first()
    db.close()
    
    if not post:
        print("No posts found with > 5 replies.")
        return
        
    post_id = post.post_id
    print(f"Testing reply fetch on post_id: {post_id}")
    
    try:
        replies = await twitter_service.fetch_tweet_replies(post_id, max_replies=10)
        print(f"Got {len(replies)} replies")
        for r in replies[:3]:
            print(r)
    except Exception as e:
        print(f"Error fetching replies: {e}")

asyncio.run(test())
