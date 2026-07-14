from fastapi import status
from app.models.enums import UserRole
from app.models.company import Company
from app.models.user import User


def test_register_candidate(client, db):
    """
    Test successful candidate registration. Must succeed with no company.
    """
    payload = {
        "email": "test_candidate@example.com",
        "password": "securepassword",
        "role": UserRole.CANDIDATE.value
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["role"] == UserRole.CANDIDATE.value
    assert data["company_id"] is None


def test_register_candidate_with_company_fails(client):
    """
    Test candidate registration fails if company parameters are supplied.
    """
    payload = {
        "email": "test_candidate@example.com",
        "password": "securepassword",
        "role": UserRole.CANDIDATE.value,
        "company_name": "Invalid Company"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Candidates cannot belong to a company" in response.json()["detail"]


def test_register_recruiter_new_company(client, db):
    """
    Test successful recruiter registration creating a new company on-the-fly.
    """
    payload = {
        "email": "test_recruiter@companyxyz.com",
        "password": "securepassword",
        "role": UserRole.RECRUITER.value,
        "company_name": "Company XYZ"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["company_id"] is not None

    # Verify company was created
    company = db.query(Company).filter(Company.name == "Company XYZ").first()
    assert company is not None
    assert str(company.id) == data["company_id"]


def test_register_recruiter_existing_company(client, db, company_a):
    """
    Test successful recruiter registration joining an existing company.
    """
    payload = {
        "email": "test_recruiter@companya.com",
        "password": "securepassword",
        "role": UserRole.RECRUITER.value,
        "company_id": str(company_a.id)
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["company_id"] == str(company_a.id)


def test_register_recruiter_without_company_fails(client):
    """
    Test recruiter registration fails if no company details are provided.
    """
    payload = {
        "email": "test_recruiter@companya.com",
        "password": "securepassword",
        "role": UserRole.RECRUITER.value
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_login_successful(client, db, candidate_user):
    """
    Test login returns JWT token on valid credentials.
    """
    payload = {
        "email": candidate_user.email,
        "password": "password123"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client, db, candidate_user):
    """
    Test login returns 401 on incorrect password.
    """
    payload = {
        "email": candidate_user.email,
        "password": "wrongpassword"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
