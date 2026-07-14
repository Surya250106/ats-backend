from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.auth.jwt import decode_access_token

# Define standard OAuth2 scheme for extracting Bearer tokens
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    auto_error=False
)


def get_current_user(token: str | None = Depends(oauth2_scheme)) -> dict:
    """
    Extracts the current user session payload from the JWT access token.
    Raises 401 Unauthorized if the token is missing or invalid.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"}
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return payload


class RequireRoles:
    """
    FastAPI dependency factory that enforces role restrictions.
    """
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: dict = Depends(get_current_user)) -> dict:
        role = current_user.get("role")
        if role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of the roles: {self.allowed_roles}"
            )
        return current_user


def require_roles(*allowed_roles: str) -> RequireRoles:
    """
    Utility dependency helper for route definitions.
    Example: Depends(require_roles("recruiter", "hiring_manager"))
    """
    return RequireRoles(list(allowed_roles))
