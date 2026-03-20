import asyncio
from twikit import Client

async def test():
    client = Client('en-US')
    # Try fetching a known tweet without logging in!
    post_id = "1879743577747804473" # Example post ID or we could fetch from DB
    try:
        print(f"Trying guest fetch on {post_id}")
        tweet = await client.get_tweet_by_id(post_id)
        print("Success! Got tweet:", tweet.text if hasattr(tweet, 'text') else tweet)
    except Exception as e:
        print("Guest fetch failed:", e)

asyncio.run(test())
