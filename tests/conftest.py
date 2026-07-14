import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database.base import Base
import app.models  # noqa: F401
from app.database.session import get_db
from app.main import app
from app.queue.celery_app import celery_app

# Run celery tasks synchronously in tests without Redis
celery_app.conf.task_always_eager = True

from app.auth.passwd import hash_password
from app.auth.jwt import create_access_token
from app.models.company import Company
from app.models.user import User
from app.models.enums import UserRole

# Ensure SQLite enforces foreign key constraints during tests
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Use StaticPool to ensure all connections in the pool share the same in-memory SQLite database instance
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@pytest.fixture(scope="function")
def db():
    """
    Sets up a fresh in-memory database and drops it after each test.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """
    FastAPI TestClient with overridden database session dependency.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def company_a(db) -> Company:
    company = Company(name="Company A")
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@pytest.fixture(scope="function")
def company_b(db) -> Company:
    company = Company(name="Company B")
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@pytest.fixture(scope="function")
def candidate_user(db) -> User:
    user = User(
        email="candidate@example.com",
        password_hash=hash_password("password123"),
        role=UserRole.CANDIDATE,
        company_id=None
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def recruiter_a(db, company_a) -> User:
    user = User(
        email="recruiter_a@companya.com",
        password_hash=hash_password("password123"),
        role=UserRole.RECRUITER,
        company_id=company_a.id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def recruiter_b(db, company_b) -> User:
    user = User(
        email="recruiter_b@companyb.com",
        password_hash=hash_password("password123"),
        role=UserRole.RECRUITER,
        company_id=company_b.id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def manager_a(db, company_a) -> User:
    user = User(
        email="manager_a@companya.com",
        password_hash=hash_password("password123"),
        role=UserRole.HIRING_MANAGER,
        company_id=company_a.id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def candidate_headers(candidate_user) -> dict:
    payload = {
        "sub": str(candidate_user.id),
        "role": candidate_user.role.value,
        "company_id": None
    }
    token = create_access_token(payload)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def recruiter_a_headers(recruiter_a) -> dict:
    payload = {
        "sub": str(recruiter_a.id),
        "role": recruiter_a.role.value,
        "company_id": str(recruiter_a.company_id)
    }
    token = create_access_token(payload)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def recruiter_b_headers(recruiter_b) -> dict:
    payload = {
        "sub": str(recruiter_b.id),
        "role": recruiter_b.role.value,
        "company_id": str(recruiter_b.company_id)
    }
    token = create_access_token(payload)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def manager_a_headers(manager_a) -> dict:
    payload = {
        "sub": str(manager_a.id),
        "role": manager_a.role.value,
        "company_id": str(manager_a.company_id)
    }
    token = create_access_token(payload)
    return {"Authorization": f"Bearer {token}"}
