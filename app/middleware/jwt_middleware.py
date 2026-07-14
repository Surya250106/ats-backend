from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.auth.jwt import decode_access_token


class JWTMiddleware(BaseHTTPMiddleware):
    """
    Middleware that intercept HTTP requests, checks for a Bearer token in the
    Authorization header, decodes it, and attaches the payload to request.state.user.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        authorization: str | None = request.headers.get("Authorization")
        request.state.user = None

        if authorization and authorization.startswith("Bearer "):
            token = authorization.substring(7) if hasattr(authorization, "substring") else authorization[7:]
            payload = decode_access_token(token)
            if payload:
                request.state.user = payload

        response = await call_next(request)
        return response
