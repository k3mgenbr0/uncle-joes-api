import logging

from app.core.errors import NotFoundError
from app.repositories.members import MemberRepository
from app.schemas.member import Member, MemberPoints


logger = logging.getLogger(__name__)


class MemberService:
    def __init__(self, repository: MemberRepository) -> None:
        self._repository = repository

    def get_member(self, member_id: str) -> Member:
        row = self._repository.get_member_by_id(member_id)
        if row is None:
            raise NotFoundError(f"Member '{member_id}' was not found.")
        return Member.model_validate(row)

    def get_points(self, member_id: str, points: int) -> MemberPoints:
        logger.info("Calculated points member_id=%s points=%s", member_id, points)
        return MemberPoints(member_id=member_id, total_points=points)
