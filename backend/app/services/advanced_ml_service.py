"""
Adapter for exposing the experimental ml_pipeline through the live FastAPI app.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import logging
import sys
from collections import Counter
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional

from app.services.text_normalization import repair_mojibake

logger = logging.getLogger(__name__)


class AdvancedMLService:
    """Lazy wrapper around the experimental political discourse pipeline."""

    REQUIRED_MODULES = {
        "pandas": "pandas",
        "torch": "torch",
        "transformers": "transformers",
        "bertopic": "bertopic",
        "sentence_transformers": "sentence-transformers",
    }
    MIN_ALIGNMENT_SAMPLES = 50
    MAX_CACHE_ENTRIES = 8

    def __init__(self) -> None:
        self.pipeline = None
        self.initialized = False
        self.init_error: Optional[str] = None
        self._lock = RLock()
        self._alignment_training_summary: Optional[Dict[str, Any]] = None
        self._analysis_cache: Dict[str, Dict[str, Any]] = {}

    def _pipeline_root(self) -> Path:
        return Path(__file__).resolve().parents[2] / "ml_pipeline"

    def status(self) -> Dict[str, Any]:
        missing = [
            package_name
            for module_name, package_name in self.REQUIRED_MODULES.items()
            if importlib.util.find_spec(module_name) is None
        ]
        return {
            "available": not missing,
            "initialized": self.initialized,
            "missing_dependencies": missing,
            "init_error": self.init_error,
        }

    def _ensure_pipeline_on_path(self) -> None:
        pipeline_root = str(self._pipeline_root())
        if pipeline_root not in sys.path:
            sys.path.insert(0, pipeline_root)

    def _init_pipeline(self) -> bool:
        with self._lock:
            if self.initialized and self.pipeline is not None:
                return True

            status = self.status()
            if not status["available"]:
                self.init_error = (
                    "Advanced ML pipeline dependencies are missing: "
                    + ", ".join(status["missing_dependencies"])
                )
                return False

            try:
                self._ensure_pipeline_on_path()
                from main_pipeline import PoliticalDiscoursePipeline

                self.pipeline = PoliticalDiscoursePipeline()
                self.initialized = True
                self.init_error = None
                logger.info("Advanced ML pipeline initialized successfully")
                return True
            except Exception as exc:
                logger.exception("Failed to initialize advanced ML pipeline")
                self.init_error = str(exc)
                self.pipeline = None
                self.initialized = False
                return False

    def _train_alignment_model_if_needed(self, db_session) -> Dict[str, Any]:
        if not self._init_pipeline():
            return {
                "status": "unavailable",
                "reason": self.init_error or "Advanced ML pipeline unavailable",
            }

        with self._lock:
            if getattr(self.pipeline.alignment_model, "is_trained", False):
                return self._alignment_training_summary or {
                    "status": "ready",
                    "reason": "Advanced alignment model already trained",
                }

            from app.models.social_media import TwitterPost

            political_posts = (
                db_session.query(TwitterPost.content, TwitterPost.party)
                .filter(TwitterPost.source_type == "political")
                .filter(TwitterPost.party.isnot(None))
                .all()
            )

            texts: List[str] = []
            labels: List[str] = []
            for content, party in political_posts:
                repaired = repair_mojibake(content)
                if repaired:
                    texts.append(repaired)
                    labels.append(party)

            if len(texts) < self.MIN_ALIGNMENT_SAMPLES:
                self._alignment_training_summary = {
                    "status": "skipped",
                    "samples": len(texts),
                    "reason": (
                        f"Need at least {self.MIN_ALIGNMENT_SAMPLES} political posts to "
                        "train the advanced alignment classifier"
                    ),
                }
                return self._alignment_training_summary

            report = self.pipeline.alignment_model.train(texts, labels)
            self._alignment_training_summary = {
                "status": "trained",
                "samples": len(texts),
                "reason": "Advanced alignment classifier trained from political Twitter posts",
                "report": report,
            }
            return self._alignment_training_summary

    def _build_cache_key(
        self,
        rows: List[Dict[str, Any]],
        topic_limit: int,
        sample_limit: int,
    ) -> str:
        digest = hashlib.sha1()
        digest.update(f"{topic_limit}:{sample_limit}:{len(rows)}".encode("utf-8"))

        for row in rows:
            posted_at = row.get("posted_at")
            digest.update(str(row.get("post_id")).encode("utf-8"))
            digest.update(b"|")
            digest.update((posted_at.isoformat() if posted_at else "").encode("utf-8"))
            digest.update(b"|")
            digest.update(str(row.get("platform") or "").encode("utf-8"))
            digest.update(b"|")
            digest.update(str(row.get("party") or "").encode("utf-8"))
            digest.update(b"|")
            digest.update(row.get("text", "").encode("utf-8", errors="ignore"))
            digest.update(b"\n")

        return digest.hexdigest()

    def _get_cached_analysis(self, cache_key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            cached = self._analysis_cache.get(cache_key)
            return copy.deepcopy(cached) if cached else None

    def _store_cached_analysis(self, cache_key: str, result: Dict[str, Any]) -> None:
        with self._lock:
            self._analysis_cache[cache_key] = copy.deepcopy(result)
            while len(self._analysis_cache) > self.MAX_CACHE_ENTRIES:
                oldest_key = next(iter(self._analysis_cache))
                self._analysis_cache.pop(oldest_key, None)

    def analyze_posts(
        self,
        db_session,
        posts: List[Dict[str, Any]],
        topic_limit: int = 5,
        sample_limit: int = 12,
    ) -> Dict[str, Any]:
        if not posts:
            return {
                "available": False,
                "error": "No posts provided for advanced analysis",
            }

        if not self._init_pipeline():
            status = self.status()
            return {
                "available": False,
                "error": self.init_error or "Advanced ML pipeline unavailable",
                "missing_dependencies": status["missing_dependencies"],
            }

        alignment_training = self._train_alignment_model_if_needed(db_session)

        import pandas as pd

        rows = []
        for post in posts:
            repaired = repair_mojibake(post.get("content"))
            if not repaired:
                continue
            rows.append(
                {
                    "post_id": post.get("post_id"),
                    "text": repaired,
                    "platform": post.get("platform"),
                    "party": post.get("party"),
                    "source_type": post.get("source_type"),
                    "posted_at": post.get("posted_at"),
                }
            )

        if not rows:
            return {
                "available": False,
                "error": "No usable text remained for advanced analysis",
            }

        cache_key = self._build_cache_key(rows, topic_limit=topic_limit, sample_limit=sample_limit)
        cached_result = self._get_cached_analysis(cache_key)
        if cached_result is not None:
            logger.info("Serving cached advanced ML analysis")
            return cached_result

        df = pd.DataFrame(rows)
        result_df = self.pipeline.run_inference_pipeline(df, text_column="text")
        if result_df.empty:
            result = {
                "available": True,
                "document_count": 0,
                "topics": [],
                "documents": [],
                "sentiment_breakdown": {},
                "alignment_breakdown": {},
                "alignment_training": alignment_training,
            }
            self._store_cached_analysis(cache_key, result)
            return result

        topic_counts = Counter(
            int(topic_id)
            for topic_id in result_df.get("topic_id", []).tolist()
            if topic_id is not None and int(topic_id) >= 0
        )

        topics = []
        total_docs = len(result_df)
        for topic_id, count in topic_counts.most_common(topic_limit):
            keywords = self.pipeline.topic_model.get_topic_keywords(topic_id)[:7]
            topic_name = (
                f"{keywords[0].capitalize()}-{keywords[1].capitalize()}"
                if len(keywords) >= 2
                else f"Topic {topic_id}"
            )
            topics.append(
                {
                    "topic_id": topic_id,
                    "topic_name": topic_name,
                    "keywords": keywords,
                    "salience_score": round(count / total_docs, 4),
                    "document_count": count,
                }
            )

        sentiment_breakdown = (
            result_df["sentiment_label"].fillna("unknown").astype(str).str.lower().value_counts().to_dict()
            if "sentiment_label" in result_df
            else {}
        )
        alignment_breakdown = (
            result_df["predicted_alignment"].fillna("Unknown").astype(str).value_counts().to_dict()
            if "predicted_alignment" in result_df
            else {}
        )

        documents = []
        sample_df = result_df.head(sample_limit) if sample_limit > 0 else result_df.head(0)
        for row in sample_df.to_dict(orient="records"):
            documents.append(
                {
                    "post_id": row.get("post_id"),
                    "platform": row.get("platform"),
                    "party": row.get("party"),
                    "source_type": row.get("source_type"),
                    "posted_at": row.get("posted_at"),
                    "clean_text": row.get("clean_text"),
                    "sentiment_label": str(row.get("sentiment_label", "")).lower(),
                    "sentiment_score": float(row.get("sentiment_score", 0.0))
                    if row.get("sentiment_score") is not None
                    else None,
                    "topic_id": int(row["topic_id"]) if row.get("topic_id") is not None else None,
                    "predicted_alignment": row.get("predicted_alignment"),
                }
            )

        result = {
            "available": True,
            "document_count": total_docs,
            "topics": topics,
            "documents": documents,
            "sentiment_breakdown": sentiment_breakdown,
            "alignment_breakdown": alignment_breakdown,
            "alignment_training": alignment_training,
        }
        self._store_cached_analysis(cache_key, result)
        return result


advanced_ml_service = AdvancedMLService()
