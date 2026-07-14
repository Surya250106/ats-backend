from fastapi import status
from app.models.job import Job
from app.models.enums import JobStatus, UserRole


def test_create_job_recruiter(client, db, recruiter_a, recruiter_a_headers):
    """
    Test successful job creation by a recruiter. The job's company_id must match the recruiter's.
    """
    payload = {
        "title": "Python Developer",
        "description": "Develop high-performance backends.",
        "status": JobStatus.OPEN.value
    }
    response = client.post("/api/jobs", json=payload, headers=recruiter_a_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["company_id"] == str(recruiter_a.company_id)
    assert data["created_by"] == str(recruiter_a.id)


def test_create_job_candidate_forbidden(client, db, candidate_headers):
    """
    Test candidate is forbidden from creating jobs.
    """
    payload = {
        "title": "Python Developer",
        "description": "Develop high-performance backends."
    }
    response = client.post("/api/jobs", json=payload, headers=candidate_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_jobs_candidate_sees_all_open(client, db, company_a, company_b, recruiter_a, recruiter_b, candidate_headers):
    """
    Test candidate can see open jobs across different companies, but not closed ones.
    """
    job_1 = Job(title="Job A1 Open", description="A detailed job description.", status=JobStatus.OPEN, company_id=company_a.id, created_by=recruiter_a.id)
    job_2 = Job(title="Job A2 Closed", description="A detailed job description.", status=JobStatus.CLOSED, company_id=company_a.id, created_by=recruiter_a.id)
    job_3 = Job(title="Job B1 Open", description="A detailed job description.", status=JobStatus.OPEN, company_id=company_b.id, created_by=recruiter_b.id)
    db.add_all([job_1, job_2, job_3])
    db.commit()

    response = client.get("/api/jobs", headers=candidate_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2  # Only job_1 and job_3 (open ones)
    titles = [item["title"] for item in data]
    assert "Job A1 Open" in titles
    assert "Job B1 Open" in titles
    assert "Job A2 Closed" not in titles


def test_get_jobs_recruiter_sees_only_own_company(client, db, company_a, company_b, recruiter_a, recruiter_b, recruiter_a_headers):
    """
    Test recruiter can only list jobs within their company (both open and closed).
    """
    job_1 = Job(title="Job A1 Open", description="A detailed job description.", status=JobStatus.OPEN, company_id=company_a.id, created_by=recruiter_a.id)
    job_2 = Job(title="Job A2 Closed", description="A detailed job description.", status=JobStatus.CLOSED, company_id=company_a.id, created_by=recruiter_a.id)
    job_3 = Job(title="Job B1 Open", description="A detailed job description.", status=JobStatus.OPEN, company_id=company_b.id, created_by=recruiter_b.id)
    db.add_all([job_1, job_2, job_3])
    db.commit()

    response = client.get("/api/jobs", headers=recruiter_a_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2  # job_1 and job_2
    titles = [item["title"] for item in data]
    assert "Job A1 Open" in titles
    assert "Job A2 Closed" in titles
    assert "Job B1 Open" not in titles


def test_update_job_recruiter_same_company(client, db, company_a, recruiter_a, recruiter_a_headers):
    """
    Test recruiter can update jobs within their own company.
    """
    job = Job(title="Developer", description="A detailed job description.", status=JobStatus.OPEN, company_id=company_a.id, created_by=recruiter_a.id)
    db.add(job)
    db.commit()

    payload = {"title": "Senior Developer"}
    response = client.put(f"/api/jobs/{job.id}", json=payload, headers=recruiter_a_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == "Senior Developer"


def test_update_job_recruiter_different_company_forbidden(client, db, company_a, company_b, recruiter_a, recruiter_b, recruiter_a_headers):
    """
    Test recruiter is forbidden from updating jobs belonging to another company.
    """
    job = Job(title="Developer B", description="A detailed job description.", status=JobStatus.OPEN, company_id=company_b.id, created_by=recruiter_b.id)
    db.add(job)
    db.commit()

    payload = {"title": "Senior Developer"}
    response = client.put(f"/api/jobs/{job.id}", json=payload, headers=recruiter_a_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_job_different_company_forbidden(client, db, company_b, recruiter_b, recruiter_a_headers):
    """
    Test recruiter cannot delete another company's job.
    """
    job = Job(title="Developer B", description="A detailed job description.", status=JobStatus.OPEN, company_id=company_b.id, created_by=recruiter_b.id)
    db.add(job)
    db.commit()

    response = client.delete(f"/api/jobs/{job.id}", headers=recruiter_a_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
