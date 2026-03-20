"""
Test suite for reply_analysis_service and reply_pipeline.

Run with:
  cd "c:\\Users\\admin\\Desktop\\final anti\\backend"
  python test_reply_pipeline.py
"""
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_reply_analysis_service():
    print("\n─── Test 1: ReplyAnalysisService.analyze_batch() ───")
    start = time.time()
    from app.services.reply_analysis_service import ReplyAnalysisService

    svc = ReplyAnalysisService()
    ok = svc._ensure_initialized()
    load_time = time.time() - start
    print(f"Model loaded: {ok}  ({load_time:.1f}s)")
    print(f"Status: {svc.status()}")

    if not ok:
        print("SKIP: model not available.")
        return

    texts = [
        # English positive
        "Great decision by the government! Fully support this.",
        # English negative
        "This is the worst policy ever. Resign now!",
        # Neutral
        "Let's wait and see what happens next.",
        # Hindi positive (Devanagari)
        "bahut accha kaam kiya! bilkul sahi hai.",
        # Hinglish negative
        "yeh bilkul bakwaas hai, bekar sarkar chor hai!",
        # Short noise (should still be classified, just treated as neutral anchor nearest)
        "okay",
    ]

    batch_start = time.time()
    results = svc.analyze_batch(texts)
    batch_time = time.time() - batch_start
    print(f"\nBatch of {len(texts)} texts in {batch_time*1000:.0f}ms:")
    for text, result in zip(texts, results):
        print(f"  [{result['sentiment_label']:8s} {result['sentiment_score']:+.3f}]  {text[:60]}")

    assert len(results) == len(texts), "Result count mismatch"
    assert results[0]["sentiment_label"] == "positive", "Expected positive"
    assert results[1]["sentiment_label"] == "negative", "Expected negative"
    print("\n✓ analyze_batch passed")


def test_aggregate():
    print("\n─── Test 2: ReplyAnalysisService.aggregate() ───")
    from app.services.reply_analysis_service import ReplyAnalysisService

    svc = ReplyAnalysisService()

    analyzed_replies = [
        {"reply_sentiment_label": "positive", "reply_sentiment_score": 0.72, "reply_likes": 50},
        {"reply_sentiment_label": "positive", "reply_sentiment_score": 0.60, "reply_likes": 10},
        {"reply_sentiment_label": "negative", "reply_sentiment_score": -0.85, "reply_likes": 5},
        {"reply_sentiment_label": "neutral",  "reply_sentiment_score":  0.00, "reply_likes": 1},
    ]

    result = svc.aggregate(analyzed_replies)
    print(f"  Dominant label:  {result['public_sentiment_label']}")
    print(f"  Weighted score:  {result['public_sentiment_score']}")
    print(f"  Reaction summary: {result['public_reaction_summary']}")

    assert result["public_sentiment_label"] == "positive"
    assert result["public_reaction_summary"]["total"] == 4
    assert result["public_reaction_summary"]["positive"] == 2
    print("✓ aggregate passed")


def test_empty():
    print("\n─── Test 3: Edge-case — empty input ───")
    from app.services.reply_analysis_service import ReplyAnalysisService

    svc = ReplyAnalysisService()
    assert svc.analyze_batch([]) == []
    agg = svc.aggregate([])
    assert agg["public_sentiment_label"] == "neutral"
    assert agg["public_reaction_summary"]["total"] == 0
    print("✓ empty input passed")


def test_model_load_time():
    print("\n─── Test 4: Cold-start model load time ───")
    start = time.time()
    from app.services.reply_analysis_service import ReplyAnalysisService
    svc = ReplyAnalysisService()
    svc._ensure_initialized()
    elapsed = time.time() - start
    print(f"  Model ready in {elapsed:.1f}s (budget: <20s)")
    assert elapsed < 20.0, f"Model took too long to load: {elapsed:.1f}s"
    print("✓ load time OK")


if __name__ == "__main__":
    test_reply_analysis_service()
    test_aggregate()
    test_empty()
    test_model_load_time()
    print("\n══════════════════════════════════")
    print("All tests passed! ✓")
