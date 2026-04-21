from fastapi import APIRouter, Depends

from app.api.dependencies import get_member_service
from app.schemas.common import ErrorResponse
from app.schemas.rewards import RewardsProgram
from app.services.members import MemberService


router = APIRouter(prefix="/rewards", tags=["rewards"])


@router.get(
    "/program",
    response_model=RewardsProgram,
    responses={500: {"model": ErrorResponse}},
    summary="Get rewards program metadata",
)
def rewards_program(
    member_service: MemberService = Depends(get_member_service),
) -> RewardsProgram:
    return RewardsProgram.model_validate(member_service.get_rewards_program())
