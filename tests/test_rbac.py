from fastapi import status
from app.models.job import Job
from app.models.application import Application
from app.models.enums import JobStatus


def test_candidate_cannot_create_jobs(client, candidate_headers):
    """
    Candidate role must be blocked from job creation (HTTP 403).
    """
    payload = {
        "title": "Blocked Job",
        "description": "This should fail",
        "status": JobStatus.OPEN.value
    }
    response = client.post("/api/jobs", json=payload, headers=candidate_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_candidate_cannot_update_stages(client, db, company_a, recruiter_a, candidate_user, candidate_headers):
    """
    Candidate role must be blocked from updating stages of applications (HTTP 403).
    """
    job = Job(title="Dev", description="A detailed job description.", status=JobStatus.OPEN, company_id=company_a.id, created_by=recruiter_a.id)
    db.add(job)
    db.flush()

    app = Application(job_id=job.id, candidate_id=candidate_user.id, stage="Applied")
    db.add(app)
    db.commit()

    payload = {"stage": "Screening"}
    response = client.put(f"/api/applications/{app.id}/stage", json=payload, headers=candidate_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_recruiter_cannot_edit_other_company_jobs(client, db, company_b, recruiter_b, recruiter_a_headers):
    """
    Recruiter from Company A must be blocked from editing a job belonging to Company B (HTTP 403).
    """
    job = Job(title="Company B Job", description="A detailed job description.", status=JobStatus.OPEN, company_id=company_b.id, created_by=recruiter_b.id)
    db.add(job)
    db.commit()

    payload = {"title": "Hacked Title"}
    response = client.put(f"/api/jobs/{job.id}", json=payload, headers=recruiter_a_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_manager_cannot_update_other_company_application_stage(client, db, company_b, recruiter_b, candidate_user, manager_a_headers):
    """
    Hiring Manager from Company A must be blocked from updating application stages for Company B's jobs.
    """
    job = Job(title="Company B Job", description="A detailed job description.", status=JobStatus.OPEN, company_id=company_b.id, created_by=recruiter_b.id)
    db.add(job)
    db.flush()

    app = Application(job_id=job.id, candidate_id=candidate_user.id, stage="Applied")
    db.add(app)
    db.commit()

    payload = {"stage": "Screening"}
    response = client.put(f"/api/applications/{app.id}/stage", json=payload, headers=manager_a_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_unauthenticated_request_fails(client):
    """
    Request without authorization token must return 401 Unauthorized.
    """
    response = client.get("/api/jobs")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
