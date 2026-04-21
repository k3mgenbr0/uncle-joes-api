from pydantic import BaseModel, Field


class RewardTier(BaseModel):
    name: str
    min_points: int


class RewardThreshold(BaseModel):
    name: str
    points_required: int


class BonusProgram(BaseModel):
    id: str
    title: str
    description: str
    start_date: str | None = None
    end_date: str | None = None
    active: bool = False


class MemberRewardsSummary(BaseModel):
    member_id: str
    current_points: int
    lifetime_points: int
    rewards_tier: str
    points_to_next_reward: int
    next_tier_name: str | None = None
    current_tier_min_points: int
    next_tier_min_points: int | None = None
    next_reward_threshold: int
    current_reward_progress: int
    points_earned_last_30_days: int
    points_earned_last_90_days: int
    bonus_programs: list[BonusProgram] = Field(default_factory=list)


class MemberRewardsRedemption(BaseModel):
    redemption_id: str
    redeemed_at: str | None = None
    reward_name: str
    points_used: int
    status: str


class MemberRewardsRedemptionList(BaseModel):
    redemptions: list[MemberRewardsRedemption] = Field(default_factory=list)
    redemption_tracking_enabled: bool = False


class RewardsProgram(BaseModel):
    points_rule: str
    tiers: list[RewardTier] = Field(default_factory=list)
    reward_thresholds: list[RewardThreshold] = Field(default_factory=list)
    bonus_programs: list[BonusProgram] = Field(default_factory=list)
