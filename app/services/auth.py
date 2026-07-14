from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.passwd import hash_password, verify_password
from app.auth.jwt import create_access_token
from app.models.enums import UserRole
from app.models.company import Company
from app.models.user import User
from app.repositories.user import user_repository
from app.repositories.company import company_repository
from app.schemas.user import UserCreate
from app.schemas.auth import LoginRequest, Token


class AuthService:
    def register_user(self, db: Session, user_in: UserCreate) -> User:
        """
        Registers a new user. Enforces RBAC and company validation.
        """
        # 1. Check if email already exists
        existing_user = user_repository.get_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered"
            )

        # 2. Validate company mapping by role
        resolved_company_id = None

        if user_in.role == UserRole.CANDIDATE:
            # Candidates must not belong to a company
            if user_in.company_id is not None or user_in.company_name is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Candidates cannot belong to a company"
                )
        else:
            # Recruiters and Hiring Managers MUST belong to a company
            if not user_in.company_id and not user_in.company_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Recruiters and hiring managers must specify a company_id or company_name"
                )

            if user_in.company_id:
                # Check if company exists
                company = company_repository.get(db, id=user_in.company_id)
                if not company:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="The specified company does not exist"
                    )
                resolved_company_id = company.id
            elif user_in.company_name:
                # Check if company name already exists, if so join it, otherwise create
                existing_company = company_repository.get_by_name(db, name=user_in.company_name)
                if existing_company:
                    resolved_company_id = existing_company.id
                else:
                    # Create new company
                    new_company = Company(name=user_in.company_name)
                    new_company = company_repository.create(db, obj_in=new_company)
                    resolved_company_id = new_company.id

        # 3. Create user
        hashed = hash_password(user_in.password)
        db_user = User(
            email=user_in.email,
            password_hash=hashed,
            role=user_in.role,
            company_id=resolved_company_id
        )
        return user_repository.create(db, obj_in=db_user)

    def login_user(self, db: Session, login_in: LoginRequest) -> Token:
        """
        Authenticates a user and returns a signed JWT token.
        """
        db_user = user_repository.get_by_email(db, email=login_in.email)
        if not db_user or not verify_password(login_in.password, db_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Build payload with user ID, role, and company ID (which can be null)
        token_payload = {
            "sub": str(db_user.id),
            "role": db_user.role.value,
            "company_id": str(db_user.company_id) if db_user.company_id else None
        }
        access_token = create_access_token(data=token_payload)

        return Token(access_token=access_token, token_type="bearer")


auth_service = AuthService()
