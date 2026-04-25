"""
Daily job sync: scrape hh.uz -> extract skills -> save to DB.
Usage:
    python manage.py sync_jobs
    python manage.py sync_jobs --full          # backfill all open vacancies
    python manage.py sync_jobs --date 2026-04-20
"""

from datetime import date, timedelta
import logging
import sys

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from services.job_scraper_service import ExtractionService


class Command(BaseCommand):
    help = "Daily job sync: scrape hh.uz -> extract skills -> save to DB."

    @staticmethod
    def _enable_live_progress_logging():
        """Print long-running scraper progress to console."""
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )

        for logger_name in ("services.job_scraper_service", "services.hh_api_client"):
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.INFO)

            has_stream = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
            if not has_stream:
                handler = logging.StreamHandler(sys.stdout)
                handler.setFormatter(formatter)
                logger.addHandler(handler)

    def add_arguments(self, parser):
        parser.add_argument(
            "--full",
            action="store_true",
            help="Backfill all open vacancies (no period filter).",
        )
        parser.add_argument(
            "--date",
            type=str,
            help="Run date in YYYY-MM-DD (used for ExtractionRun tracking).",
        )

    def handle(self, *args, **options):
        self._enable_live_progress_logging()

        full = bool(options.get("full"))
        run_date = None

        if options.get("date"):
            try:
                run_date = date.fromisoformat(options["date"])
            except Exception:
                raise CommandError("Invalid --date. Expected YYYY-MM-DD.")

        if full:
            self.stdout.write(
                self.style.WARNING(
                    "Running FULL sync. This can take a long time. "
                    "Live progress logs are enabled below."
                )
            )

        try:
            service = ExtractionService(source="hh.uz")
            run = service.run(run_date=run_date, trigger="manual", full=full)
        except KeyboardInterrupt:
            raise CommandError("sync_jobs interrupted by user (Ctrl+C).")
        except Exception as e:
            raise CommandError(f"sync_jobs failed: {e}")

        # If an old run is stuck in "running", recover automatically for manual use.
        if run.status == "running":
            stale_after = timedelta(minutes=15)
            started_at = run.started_at
            now = timezone.now()
            is_stale = not started_at or (now - started_at) > stale_after

            if is_stale:
                self.stdout.write(
                    self.style.WARNING(
                        f"Stale running run found for {run.run_date} (started_at={started_at}). "
                        "Marking failed and retrying once..."
                    )
                )
                run.status = "failed"
                run.finished_at = now
                if not run.error_message:
                    run.error_message = "Marked failed by sync_jobs stale-run recovery."
                run.save(update_fields=["status", "finished_at", "error_message"])
                try:
                    run = service.retry(run_date=run.run_date, source="hh.uz", full=full)
                except KeyboardInterrupt:
                    raise CommandError("sync_jobs retry interrupted by user (Ctrl+C).")
                except Exception as e:
                    raise CommandError(f"sync_jobs retry failed after stale-run recovery: {e}")
            else:
                raise CommandError(
                    f"sync_jobs is already running for {run.run_date} "
                    f"(started_at={started_at}). Wait for it to finish or try later."
                )

        # If a failed run already existed for this date, run() returns it due to
        # unique (source, run_date). For manual sync, retry once automatically.
        if run.status == "failed":
            self.stdout.write(
                self.style.WARNING(
                    f"Existing failed run found for {run.run_date}. Retrying once..."
                )
            )
            try:
                run = service.retry(run_date=run.run_date, source="hh.uz", full=full)
            except KeyboardInterrupt:
                raise CommandError("sync_jobs retry interrupted by user (Ctrl+C).")
            except Exception as e:
                raise CommandError(f"sync_jobs retry failed: {e}")

        # If a run already existed for this date (unique constraint), `run` may be an
        # earlier failed record. Per requirements, exit non-zero on failure and show why.
        if run.status != "success":
            if run.status == "running":
                msg = "Extraction run is currently running."
            else:
                msg = (run.error_message or "Extraction run failed. Check logs.").strip()
            raise CommandError(f"sync_jobs finished with status={run.status}: {msg}")

        self.stdout.write(self.style.SUCCESS("\nJob sync completed"))
        self.stdout.write(f"  source:         {run.source}")
        self.stdout.write(f"  run_date:       {run.run_date}")
        self.stdout.write(f"  status:         {run.status}")
        self.stdout.write(f"  jobs_created:   {run.jobs_created}")
        self.stdout.write(f"  jobs_updated:   {run.jobs_updated}")
        self.stdout.write(f"  jobs_deactivated: {run.jobs_deactivated}")
        self.stdout.write(f"  errors:         {run.errors_count}")
