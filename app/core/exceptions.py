from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Register application-wide exception handlers for consistent error formatting.
    Ensures that validation errors return HTTP 422 with a structured 'detail' string.
    """
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Format multi-field validation error details into a single readable string
        error_messages = []
        for error in exc.errors():
            location = ".".join(str(loc) for loc in error["loc"] if loc != "body")
            message = error["msg"]
            error_messages.append(f"{location}: {message}" if location else message)

        formatted_detail = "Validation failed: " + "; ".join(error_messages)

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": formatted_detail}
        )
