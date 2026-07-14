from fastapi import status
from unittest.mock import patch
import uuid
from app.models.job import Job
from app.models.user import User
from app.models.application import Application
from app.models.history import ApplicationHistory
from app.models.enums import JobStatus, UserRole


@patch("app.workers.tasks.send_application_submitted_email.delay")
@patch("app.workers.tasks.send_recruiter_notification_email.delay")
def test_apply_to_job(mock_recruiter_notify, mock_candidate_notify, client, db, company_a, recruiter_a, candidate_user, candidate_headers):
    """
    Test candidate applying to a job successfully. Must create application and history, and queue emails.
    """
    job = Job(title="Dev", description="A detailed job description.", status=JobStatus.OPEN, company_id=company_a.id, created_by=recruiter_a.id)
    db.add(job)
    db.commit()

    payload = {"resume_url": "http://example.com/resume.pdf"}
    response = client.post(f"/api/jobs/{job.id}/applications", json=payload, headers=candidate_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["stage"] == "Applied"
    assert data["resume_url"] == payload["resume_url"]

    # Verify Application and History are created
    app_db = db.query(Application).filter(Application.id == uuid.UUID(data["id"])).first()
    assert app_db is not None
    assert app_db.stage == "Applied"

    histories = db.query(ApplicationHistory).filter(ApplicationHistory.application_id == app_db.id).all()
    assert len(histories) == 1
    assert histories[0].previous_stage is None
    assert histories[0].new_stage == "Applied"
    assert histories[0].changed_by == candidate_user.id

    # Verify background tasks are enqueued
    mock_candidate_notify.assert_called_once_with(candidate_user.email, job.title)
    mock_recruiter_notify.assert_called_once_with(recruiter_a.email, candidate_user.email, job.title)


def test_apply_to_job_duplicate_conflict(client, db, company_a, recruiter_a, candidate_user, candidate_headers):
    """
    Test duplicate application to the same job fails with 409 Conflict.
    """
    job = Job(title="Dev", description="A detailed job description.", status=JobStatus.OPEN, company_id=company_a.id, created_by=recruiter_a.id)
    db.add(job)
    db.commit()

    # First application
    app_in = Application(job_id=job.id, candidate_id=candidate_user.id, stage="Applied")
    db.add(app_in)
    db.commit()

    payload = {"resume_url": "http://example.com/resume.pdf"}
    response = client.post(f"/api/jobs/{job.id}/applications", json=payload, headers=candidate_headers)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "already applied" in response.json()["detail"]


def test_get_my_applications_candidate(client, db, company_a, recruiter_a, candidate_user, candidate_headers):
    """
    Test candidate can list their own applications.
    """
    job = Job(title="Dev", description="A detailed job description.", status=JobStatus.OPEN, company_id=company_a.id, created_by=recruiter_a.id)
    db.add(job)
    db.commit()

    app_in = Application(job_id=job.id, candidate_id=candidate_user.id, stage="Applied")
    db.add(app_in)
    db.commit()

    response = client.get("/api/applications/me", headers=candidate_headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == str(app_in.id)


def test_get_application_by_id_candidate_ownership(client, db, company_a, recruiter_a, candidate_user, candidate_headers, recruiter_a_headers, recruiter_b_headers):
    """
    Test candidate can view own application details, and recruiter of job company can view, but recruiter of other company cannot.
    """
    job = Job(title="Dev", description="A detailed job description.", status=JobStatus.OPEN, company_id=company_a.id, created_by=recruiter_a.id)
    db.add(job)
    db.commit()

    app_in = Application(job_id=job.id, candidate_id=candidate_user.id, stage="Applied")
    db.add(app_in)
    db.commit()

    # 1. Candidate views own (Succeeds)
    response = client.get(f"/api/applications/{app_in.id}", headers=candidate_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(app_in.id)

    # 2. Recruiter A views (Succeeds because it belongs to Company A)
    response = client.get(f"/api/applications/{app_in.id}", headers=recruiter_a_headers)
    assert response.status_code == status.HTTP_200_OK

    # 3. Recruiter B views (Fails because it belongs to Company A, and recruiter B belongs to Company B)
    response = client.get(f"/api/applications/{app_in.id}", headers=recruiter_b_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_job_applications_stage_filtering(client, db, company_a, recruiter_a, candidate_user, recruiter_a_headers):
    """
    Test recruiter can list applications for a job, and stage filtering works.
    """
    job = Job(title="Dev", description="A detailed job description.", status=JobStatus.OPEN, company_id=company_a.id, created_by=recruiter_a.id)
    db.add(job)
    db.commit()

    # Create two applications with different stages
    app_1 = Application(job_id=job.id, candidate_id=candidate_user.id, stage="Applied")

    # Create another candidate
    other_candidate = User(
        email="other@example.com",
        password_hash="pw",
        role=UserRole.CANDIDATE,
        company_id=None
    )
    db.add(other_candidate)
    db.flush()

    app_2 = Application(job_id=job.id, candidate_id=other_candidate.id, stage="Screening")
    db.add_all([app_1, app_2])
    db.commit()

    # 1. Get all
    response = client.get(f"/api/jobs/{job.id}/applications", headers=recruiter_a_headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2

    # 2. Filter by stage = Screening
    response = client.get(f"/api/jobs/{job.id}/applications?stage=Screening", headers=recruiter_a_headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["stage"] == "Screening"
