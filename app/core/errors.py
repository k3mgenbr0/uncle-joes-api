import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.common import ErrorResponse


logger = logging.getLogger(__name__)


class NotFoundError(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class DatabaseError(Exception):
    def __init__(self, detail: str = "Database query failed.") -> None:
        self.detail = detail
        super().__init__(detail)


class UnauthorizedError(Exception):
    def __init__(self, detail: str = "Unauthorized.") -> None:
        self.detail = detail
        super().__init__(detail)


class BadRequestError(Exception):
    def __init__(self, detail: str = "Bad request.") -> None:
        self.detail = detail
        super().__init__(detail)


def _error_response(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(detail=detail).model_dump(),
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def handle_not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return _error_response(status.HTTP_404_NOT_FOUND, exc.detail)

    @app.exception_handler(DatabaseError)
    async def handle_database_error(_: Request, exc: DatabaseError) -> JSONResponse:
        logger.exception("Database error: %s", exc.detail)
        return _error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, exc.detail)

    @app.exception_handler(UnauthorizedError)
    async def handle_unauthorized(_: Request, exc: UnauthorizedError) -> JSONResponse:
        return _error_response(status.HTTP_401_UNAUTHORIZED, exc.detail)

    @app.exception_handler(BadRequestError)
    async def handle_bad_request(_: Request, exc: BadRequestError) -> JSONResponse:
        return _error_response(status.HTTP_400_BAD_REQUEST, exc.detail)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled application error", exc_info=exc)
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal server error.",
        )
