from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    kind: str
    id: str
    label: str
    subtitle: str | None = None
    score: float | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult] = Field(default_factory=list)
