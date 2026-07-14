from fastapi import status
from app.models.job import Job
from app.models.application import Application
from app.models.history import ApplicationHistory
from app.models.enums import JobStatus


def test_transition_applied_to_screening_pass(client, db, company_a, recruiter_a, candidate_user, recruiter_a_headers):
    """
    Applied -> Screening is a valid transition (HTTP 200).
    """
    job = Job(title="Dev", description="A detailed job description.", status=JobStatus.OPEN, company_id=company_a.id, created_by=recruiter_a.id)
    db.add(job)
    db.flush()

    app = Application(job_id=job.id, candidate_id=candidate_user.id, stage="Applied")
    db.add(app)
    db.commit()

    payload = {"stage": "Screening"}
    response = client.put(f"/api/applications/{app.id}/stage", json=payload, headers=recruiter_a_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["stage"] == "Screening"

    # Verify history entry
    history = db.query(ApplicationHistory).filter(ApplicationHistory.application_id == app.id).order_by(ApplicationHistory.changed_at.desc()).first()
    assert history is not None
    assert history.previous_stage == "Applied"
    assert history.new_stage == "Screening"


def test_transition_applied_to_offer_fail(client, db, company_a, recruiter_a, candidate_user, recruiter_a_headers):
    """
    Applied -> Offer is an invalid transition (HTTP 400).
    """
    job = Job(title="Dev", description="A detailed job description.", status=JobStatus.OPEN, company_id=company_a.id, created_by=recruiter_a.id)
    db.add(job)
    db.flush()

    app = Application(job_id=job.id, candidate_id=candidate_user.id, stage="Applied")
    db.add(app)
    db.commit()

    payload = {"stage": "Offer"}
    response = client.put(f"/api/applications/{app.id}/stage", json=payload, headers=recruiter_a_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Verify database state remained unchanged
    db.refresh(app)
    assert app.stage == "Applied"


def test_transition_interview_to_applied_fail(client, db, company_a, recruiter_a, candidate_user, recruiter_a_headers):
    """
    Interview -> Applied is an invalid backward transition (HTTP 400).
    """
    job = Job(title="Dev", description="A detailed job description.", status=JobStatus.OPEN, company_id=company_a.id, created_by=recruiter_a.id)
    db.add(job)
    db.flush()

    app = Application(job_id=job.id, candidate_id=candidate_user.id, stage="Interview")
    db.add(app)
    db.commit()

    payload = {"stage": "Applied"}
    response = client.put(f"/api/applications/{app.id}/stage", json=payload, headers=recruiter_a_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_transition_offer_to_hired_pass(client, db, company_a, recruiter_a, candidate_user, recruiter_a_headers):
    """
    Offer -> Hired is a valid transition (HTTP 200).
    """
    job = Job(title="Dev", description="A detailed job description.", status=JobStatus.OPEN, company_id=company_a.id, created_by=recruiter_a.id)
    db.add(job)
    db.flush()

    app = Application(job_id=job.id, candidate_id=candidate_user.id, stage="Offer")
    db.add(app)
    db.commit()

    payload = {"stage": "Hired"}
    response = client.put(f"/api/applications/{app.id}/stage", json=payload, headers=recruiter_a_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["stage"] == "Hired"


def test_transition_rejected_to_anything_fail(client, db, company_a, recruiter_a, candidate_user, recruiter_a_headers):
    """
    Rejected is a terminal state; any transition from Rejected must fail (HTTP 400).
    """
    job = Job(title="Dev", description="A detailed job description.", status=JobStatus.OPEN, company_id=company_a.id, created_by=recruiter_a.id)
    db.add(job)
    db.flush()

    app = Application(job_id=job.id, candidate_id=candidate_user.id, stage="Rejected")
    db.add(app)
    db.commit()

    payload = {"stage": "Interview"}
    response = client.put(f"/api/applications/{app.id}/stage", json=payload, headers=recruiter_a_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
