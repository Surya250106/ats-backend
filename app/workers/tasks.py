import logging
from app.queue.celery_app import celery_app
from app.utils.email import append_to_email_log

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=2,
    max_retries=5,
    default_retry_delay=5
)
def send_application_submitted_email(self, candidate_email: str, job_title: str) -> str:
    """
    Sends notification to candidate confirming receipt of application.
    """
    logger.info(f"Sending application submission email to {candidate_email} for job: {job_title}")
    try:
        append_to_email_log(
            to_email=candidate_email,
            subject="Application Received",
            body=f"Hello, we have successfully received your application for the position of '{job_title}'. Thank you for applying!"
        )
        return f"Successfully sent submission email to {candidate_email}"
    except Exception as exc:
        logger.error(f"Failed to log email to {candidate_email}: {exc}. Retrying...")
        raise exc


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=2,
    max_retries=5,
    default_retry_delay=5
)
def send_recruiter_notification_email(self, recruiter_email: str, candidate_email: str, job_title: str) -> str:
    """
    Sends notification to recruiter informing them of a new application.
    """
    logger.info(f"Sending recruiter notification to {recruiter_email} for candidate: {candidate_email}")
    try:
        append_to_email_log(
            to_email=recruiter_email,
            subject="New Application Received",
            body=f"Hi, candidate '{candidate_email}' has submitted a new application for the job: '{job_title}'."
        )
        return f"Successfully sent recruiter notification to {recruiter_email}"
    except Exception as exc:
        logger.error(f"Failed to log email to recruiter {recruiter_email}: {exc}. Retrying...")
        raise exc


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=2,
    max_retries=5,
    default_retry_delay=5
)
def send_stage_updated_email(self, candidate_email: str, job_title: str, previous_stage: str | None, new_stage: str) -> str:
    """
    Sends notification to candidate notifying them of their application stage update.
    """
    logger.info(f"Sending stage update email to {candidate_email} (from {previous_stage} to {new_stage})")
    try:
        prev_text = previous_stage if previous_stage else "None"
        append_to_email_log(
            to_email=candidate_email,
            subject="Application Stage Updated",
            body=f"Hello, your application status for the position '{job_title}' has transitioned from '{prev_text}' to '{new_stage}'."
        )
        return f"Successfully sent stage update email to {candidate_email}"
    except Exception as exc:
        logger.error(f"Failed to log stage update email to {candidate_email}: {exc}. Retrying...")
        raise exc
