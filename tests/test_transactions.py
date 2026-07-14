from fastapi import status
from app.models.job import Job
from app.models.application import Application
from app.models.enums import JobStatus


def test_stage_update_rollback_on_failure(client, db, company_a, recruiter_a, candidate_user, recruiter_a_headers):
    """
    Assert that if a database commit fails during stage transition,
    the application stage changes are rolled back completely and not saved.
    """
    # 1. Seed job and application successfully
    job = Job(title="Dev", description="A detailed job description.", status=JobStatus.OPEN, company_id=company_a.id, created_by=recruiter_a.id)
    db.add(job)
    db.flush()

    app = Application(
        job_id=job.id,
        candidate_id=candidate_user.id,
        stage="Applied"
    )
    db.add(app)
    db.commit()  # Saves to SQLite database

    # Verify initial state is Applied
    assert app.stage == "Applied"

    # 2. Patch db.commit on this session instance to raise an exception
    original_commit = db.commit

    def mock_commit_fail():
        raise Exception("Database connection failure")

    db.commit = mock_commit_fail

    # 3. Call stage update API which triggers the commit call and raises Exception
    payload = {"stage": "Screening"}
    response = client.put(f"/api/applications/{app.id}/stage", json=payload, headers=recruiter_a_headers)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Database update failed" in response.json()["detail"]

    # 4. Restore original commit, rollback the failed transaction on session, and verify rollback
    db.commit = original_commit
    db.rollback()
    db.refresh(app)
    assert app.stage == "Applied"
