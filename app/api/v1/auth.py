from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import LoginRequest, Token
from app.services.auth import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    """
    Register a new user (Candidate, Recruiter, or Hiring Manager).
    Candidates must not provide a company.
    Recruiters and hiring managers must join an existing company or create a new one.
    """
    return auth_service.register_user(db, user_in)


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login(login_in: LoginRequest, db: Session = Depends(get_db)) -> Token:
    """
    Log in with email and password to receive a JWT access token.
    """
    return auth_service.login_user(db, login_in)
