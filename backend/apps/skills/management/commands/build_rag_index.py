"""
Build RAG vector index for chatbot semantic search.
Usage:
    python manage.py build_rag_index           # index new items only
    python manage.py build_rag_index --full    # rebuild everything
    python manage.py build_rag_index --jobs-only
    python manage.py build_rag_index --skills-only
"""

from django.core.management.base import BaseCommand

from apps.chatbot.models import JobVector, SkillVector
from apps.chatbot.rag_indexer import RAGIndexer


class Command(BaseCommand):
    help = "Build chatbot RAG vector index."

    def add_arguments(self, parser):
        parser.add_argument(
            "--full",
            action="store_true",
            help="Delete all vector rows and rebuild from scratch.",
        )
        parser.add_argument(
            "--jobs-only",
            action="store_true",
            help="Index only job vectors.",
        )
        parser.add_argument(
            "--skills-only",
            action="store_true",
            help="Index only skill vectors.",
        )

    def handle(self, *args, **options):
        full = bool(options.get("full"))
        jobs_only = bool(options.get("jobs_only"))
        skills_only = bool(options.get("skills_only"))

        run_jobs = jobs_only or not skills_only
        run_skills = skills_only or not jobs_only

        self.stdout.write(self.style.SUCCESS("\nRAG indexing started"))

        if full:
            self.stdout.write(self.style.WARNING("Full rebuild requested: clearing existing vectors..."))
            try:
                deleted_jobs = JobVector.objects.all().delete()[0]
                deleted_skills = SkillVector.objects.all().delete()[0]
                self.stdout.write(
                    f"  Cleared vectors: job_vectors={deleted_jobs}, skill_vectors={deleted_skills}"
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Failed to clear vectors: {e}"))

        try:
            indexer = RAGIndexer()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to initialize RAG indexer: {e}"))
            return

        final_stats = {
            "jobs_indexed": 0,
            "jobs_skipped": 0,
            "skills_indexed": 0,
        }

        if run_jobs:
            self.stdout.write("\nIndexing jobs...")
            try:
                job_stats = indexer.build_job_index()
                final_stats["jobs_indexed"] = job_stats.get("indexed", 0)
                final_stats["jobs_skipped"] = job_stats.get("skipped", 0)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Jobs indexed: {final_stats['jobs_indexed']} (skipped: {final_stats['jobs_skipped']})"
                    )
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Job indexing failed: {e}"))

        if run_skills:
            self.stdout.write("\nIndexing skills...")
            try:
                skill_stats = indexer.build_skill_index()
                final_stats["skills_indexed"] = skill_stats.get("indexed", 0)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Skills indexed: {final_stats['skills_indexed']}"
                    )
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Skill indexing failed: {e}"))

        self.stdout.write("\nRAG indexing complete")
        self.stdout.write(f"  jobs_indexed:   {final_stats['jobs_indexed']}")
        self.stdout.write(f"  jobs_skipped:   {final_stats['jobs_skipped']}")
        self.stdout.write(f"  skills_indexed: {final_stats['skills_indexed']}")
