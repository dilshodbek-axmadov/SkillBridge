"""
RAG Indexer
===========
apps/chatbot/rag_indexer.py

Builds and queries vector index for semantic search.
Uses sentence-transformers (all-MiniLM-L6-v2) for embeddings.
Local model - no API calls needed.
"""

import logging
from typing import Dict, List

from django.core.cache import cache
from django.db.models import Count
from pgvector.django import CosineDistance
from sentence_transformers import SentenceTransformer

from apps.chatbot.models import JobVector, SkillVector
from apps.jobs.models import JobPosting
from apps.skills.models import Skill, MarketTrend

logger = logging.getLogger(__name__)


class RAGIndexer:
    """Builds and queries pgvector-backed semantic index."""

    MODEL_NAME = "all-MiniLM-L6-v2"
    MARKET_CACHE_KEY = "rag_market_summary"
    MARKET_CACHE_TIMEOUT = 3600
    _shared_model = None

    def __init__(self):
        # Load once per process to avoid reloading on every chat request.
        if RAGIndexer._shared_model is None:
            logger.info("Loading sentence transformer model: %s", self.MODEL_NAME)
            RAGIndexer._shared_model = SentenceTransformer(self.MODEL_NAME)
        self.model = RAGIndexer._shared_model

    def embed(self, text: str) -> list:
        """Embed text into a 384-dim vector for pgvector storage."""
        safe_text = (text or "")[:512]
        vector = self.model.encode(safe_text)
        return vector.tolist()

    def _build_job_summary(self, job: JobPosting) -> str:
        skills = [
            js.skill.name_en
            for js in job.job_skills.select_related("skill").all()
            if js.skill and js.skill.name_en
        ][:10]

        skills_text = ", ".join(skills) if skills else "N/A"
        company = job.company_name or "Unknown company"
        experience = job.experience_required or "not specified"
        location = job.location or "not specified"
        salary_min = job.salary_min if job.salary_min is not None else "N/A"
        salary_max = job.salary_max if job.salary_max is not None else "N/A"
        currency = job.salary_currency or "UZS"

        return (
            f"{job.job_title} at {company}. "
            f"Experience: {experience}. "
            f"Skills: {skills_text}. "
            f"Location: {location}. "
            f"Salary: {salary_min}-{salary_max} {currency}."
        )

    def build_job_index(self, batch_size: int = 100) -> dict:
        """Build embeddings for active jobs missing vector rows."""
        queryset = (
            JobPosting.objects.filter(is_active=True, vector__isnull=True)
            .prefetch_related("job_skills__skill")
            .order_by("job_id")
        )

        indexed = 0
        skipped = 0
        batch: List[JobVector] = []

        for job in queryset.iterator(chunk_size=batch_size):
            try:
                summary = self._build_job_summary(job)
                embedding = self.embed(summary)
                batch.append(JobVector(job=job, embedding=embedding, summary=summary))
            except Exception as e:
                skipped += 1
                logger.warning("Failed to index job %s: %s", job.job_id, e)

            if len(batch) >= batch_size:
                try:
                    JobVector.objects.bulk_create(batch, ignore_conflicts=True)
                    indexed += len(batch)
                except Exception as e:
                    logger.warning("JobVector bulk_create batch failed: %s", e)
                    for obj in batch:
                        try:
                            JobVector.objects.update_or_create(
                                job=obj.job,
                                defaults={
                                    "embedding": obj.embedding,
                                    "summary": obj.summary,
                                },
                            )
                            indexed += 1
                        except Exception as inner_e:
                            skipped += 1
                            logger.warning(
                                "Failed fallback indexing for job %s: %s",
                                obj.job_id,
                                inner_e,
                            )
                finally:
                    batch = []

        if batch:
            try:
                JobVector.objects.bulk_create(batch, ignore_conflicts=True)
                indexed += len(batch)
            except Exception as e:
                logger.warning("Final JobVector bulk_create failed: %s", e)
                for obj in batch:
                    try:
                        JobVector.objects.update_or_create(
                            job=obj.job,
                            defaults={
                                "embedding": obj.embedding,
                                "summary": obj.summary,
                            },
                        )
                        indexed += 1
                    except Exception as inner_e:
                        skipped += 1
                        logger.warning(
                            "Failed fallback indexing for job %s: %s",
                            obj.job_id,
                            inner_e,
                        )

        return {"indexed": indexed, "skipped": skipped}

    def build_skill_index(self) -> dict:
        """Build embeddings for skills missing vector rows."""
        skills = Skill.objects.filter(vector__isnull=True).order_by("skill_id")

        indexed = 0
        vectors: List[SkillVector] = []

        for skill in skills.iterator(chunk_size=500):
            try:
                text = f"{skill.name_en}. Category: {skill.category}. Also known as: {skill.name_ru or ''}"
                vectors.append(SkillVector(skill=skill, embedding=self.embed(text)))
            except Exception as e:
                logger.warning("Failed to index skill %s: %s", skill.skill_id, e)

        if vectors:
            try:
                SkillVector.objects.bulk_create(vectors, ignore_conflicts=True)
                indexed = len(vectors)
            except Exception as e:
                logger.warning("SkillVector bulk_create failed: %s", e)
                indexed = 0
                for obj in vectors:
                    try:
                        SkillVector.objects.update_or_create(
                            skill=obj.skill,
                            defaults={"embedding": obj.embedding},
                        )
                        indexed += 1
                    except Exception as inner_e:
                        logger.warning(
                            "Failed fallback indexing for skill %s: %s",
                            obj.skill_id,
                            inner_e,
                        )

        return {"indexed": indexed}

    def search_jobs(self, query: str, top_k: int = 5) -> List[Dict]:
        """Semantic job retrieval using cosine distance."""
        query_embedding = self.embed(query)

        matches = (
            JobVector.objects.select_related("job")
            .annotate(distance=CosineDistance("embedding", query_embedding))
            .order_by("distance")[:top_k]
        )

        results = []
        for item in matches:
            distance = float(item.distance) if item.distance is not None else 1.0
            results.append(
                {
                    "job_title": item.job.job_title,
                    "company_name": item.job.company_name,
                    "summary": item.summary,
                    "job_url": item.job.job_url,
                    "similarity": max(0.0, 1.0 - distance),
                }
            )

        return results

    def search_skills(self, query: str, top_k: int = 8) -> List[Dict]:
        """Semantic skill retrieval using cosine distance."""
        query_embedding = self.embed(query)

        matches = (
            SkillVector.objects.select_related("skill")
            .annotate(distance=CosineDistance("embedding", query_embedding))
            .order_by("distance")[:top_k]
        )

        results = []
        for item in matches:
            distance = float(item.distance) if item.distance is not None else 1.0
            results.append(
                {
                    "skill_id": item.skill.skill_id,
                    "name_en": item.skill.name_en,
                    "category": item.skill.category,
                    "similarity": max(0.0, 1.0 - distance),
                }
            )

        return results

    def get_market_summary(self) -> str:
        """Return cached compact market summary for prompt context."""
        cached = cache.get(self.MARKET_CACHE_KEY)
        if cached:
            return cached

        top_trends = (
            MarketTrend.objects.filter(period="30d")
            .select_related("skill")
            .order_by("-demand_score")[:10]
        )

        active_jobs = JobPosting.objects.filter(is_active=True).count()

        top_categories = (
            JobPosting.objects.filter(is_active=True)
            .values("job_category")
            .annotate(count=Count("job_id"))
            .order_by("-count")[:5]
        )

        top_skills_text = ", ".join(
            [
                f"{t.skill.name_en} (score={int(round(t.demand_score))}, {t.job_count} jobs)"
                for t in top_trends
                if t.skill_id
            ]
        ) or "No trend data"

        top_categories_text = ", ".join(
            [f"{(c['job_category'] or 'Other')} ({c['count']})" for c in top_categories]
        ) or "No category data"

        summary = (
            f"Market snapshot (Uzbekistan IT): {active_jobs} active jobs.\n"
            f"Top skills: {top_skills_text}.\n"
            f"Top categories: {top_categories_text}."
        )

        cache.set(self.MARKET_CACHE_KEY, summary, self.MARKET_CACHE_TIMEOUT)
        return summary

    def invalidate_cache(self):
        """Invalidate cached market summary."""
        cache.delete(self.MARKET_CACHE_KEY)
