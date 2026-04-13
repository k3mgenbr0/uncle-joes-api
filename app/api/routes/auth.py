"""
Uncle Joe's Coffee Company - FastAPI login example

Demonstrates how to accept credentials over HTTP, hash the submitted
password with bcrypt, and construct a parameterized BigQuery query to
look up the matching member.

Setup:
    poetry install

Run:
    poetry run uvicorn app.main:app --reload

Then POST to http://127.0.0.1:8000/login
"""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_auth_service
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.common import ErrorResponse
from app.services.auth import AuthService


router = APIRouter(tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Authenticate a Coffee Club member",
)
def login(
    body: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    return service.login(body.email, body.password)
