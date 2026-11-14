
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.database.models import MonitoringSource
from app.services.monitoring_service import scan_source


scheduler = BackgroundScheduler(timezone="Asia/Kolkata")

JOB_PREFIX = "source_scan_"


def scan_source_job(source_id: int):
    """Execute one monitoring source scan."""

    db: Session = SessionLocal()

    try:
        source = (
            db.query(MonitoringSource)
            .filter(
                MonitoringSource.id == source_id,
                MonitoringSource.active == True
            )
            .first()
        )

        if not source:
            print(f"Skipping inactive or missing source: {source_id}")
            return

        print(f"Starting scan: {source.source_name}")

        result = scan_source(db, source_id)

        print(f"Scan completed: {source.source_name}")
        print(result)

    except Exception as exc:
        print(f"Scan failed for source {source_id}: {exc}")

    finally:
        db.close()


def refresh_source_jobs():
    """Synchronize scheduled jobs with active database sources."""

    db: Session = SessionLocal()

    try:
        sources = (
            db.query(MonitoringSource)
            .filter(MonitoringSource.active == True)
            .all()
        )

        active_job_ids = {
            f"{JOB_PREFIX}{source.id}" for source in sources
        }

        # Remove jobs for deleted or inactive sources.
        for job in scheduler.get_jobs():
            if job.id.startswith(JOB_PREFIX):
                if job.id not in active_job_ids:
                    scheduler.remove_job(job.id)
                    print(f"Removed scheduled job: {job.id}")

        # Create or update jobs for active sources.
        for source in sources:
            job_id = f"{JOB_PREFIX}{source.id}"
            interval = max(1, source.scan_interval_minutes)

            existing_job = scheduler.get_job(job_id)

            if existing_job is None:
                scheduler.add_job(
                    scan_source_job,
                    trigger="interval",
                    minutes=interval,
                    args=[source.id],
                    id=job_id,
                    replace_existing=True,
                    max_instances=1,
                    coalesce=True,
                    misfire_grace_time=300
                )

                print(
                    f"Scheduled {source.source_name} "
                    f"every {interval} minutes"
                )

            else:
                current_interval = (
                    existing_job.trigger.interval.total_seconds() / 60
                )

                if current_interval != interval:
                    scheduler.reschedule_job(
                        job_id,
                        trigger="interval",
                        minutes=interval
                    )

                    print(
                        f"Updated {source.source_name} "
                        f"to every {interval} minutes"
                    )

    finally:
        db.close()


def start_scheduler():
    if scheduler.running:
        return

    # Create source-specific jobs before starting the scheduler.
    refresh_source_jobs()

    # Check for new, updated or inactive sources every minute.
    scheduler.add_job(
        refresh_source_jobs,
        trigger="interval",
        minutes=1,
        id="refresh_source_jobs",
        replace_existing=True,
        max_instances=1
    )

    scheduler.start()

    print("University monitoring scheduler started")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("University monitoring scheduler stopped")
