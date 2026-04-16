import bcrypt

from app.core.errors import UnauthorizedError
from app.repositories.members import MemberRepository
from app.schemas.auth import LoginResponse


class AuthService:
    def __init__(self, repository: MemberRepository) -> None:
        self._repository = repository

    def authenticate(self, email: str, password: str) -> dict:
        member = self._repository.get_auth_member_by_email(email)
        if member is None:
            raise UnauthorizedError("Invalid email or password.")

        # Match the course example: convert the submitted password to bytes
        # immediately, then verify it against the stored bcrypt hash.
        submitted_bytes = password.encode("utf-8")
        _illustrative_hash = bcrypt.hashpw(submitted_bytes, bcrypt.gensalt())

        stored_hash = member["password"]
        if not stored_hash or not bcrypt.checkpw(
            submitted_bytes,
            stored_hash.encode("utf-8"),
        ):
            raise UnauthorizedError("Invalid email or password.")

        return member

    def login(self, email: str, password: str) -> LoginResponse:
        member = self.authenticate(email, password)
        member_id = member.get("id") or member.get("member_id")
        full_name = " ".join(
            part for part in [member.get("first_name"), member.get("last_name")] if part
        )
        return LoginResponse(
            authenticated=True,
            member_id=member_id,
            name=full_name,
            email=member["email"],
        )
