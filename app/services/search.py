import logging
from difflib import SequenceMatcher

from app.repositories.search import SearchRepository
from app.schemas.search import SearchResponse, SearchResult


logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self, repository: SearchRepository) -> None:
        self._repository = repository

    def search(
        self,
        query: str,
        limit: int,
        scope: str,
        location_filters: dict | None = None,
        menu_filters: dict | None = None,
        fuzzy: bool = True,
        min_score: float = 0.0,
    ) -> SearchResponse:
        location_rows = []
        menu_rows = []
        scope_value = scope.lower()
        if scope_value in ("all", "locations"):
            location_rows = self._repository.search_locations(
                query,
                limit,
                filters=location_filters,
            )
        if scope_value in ("all", "menu"):
            menu_rows = self._repository.search_menu(
                query,
                limit,
                filters=menu_filters,
            )

        results: list[SearchResult] = []
        query_normalized = query.strip().lower()
        for row in location_rows:
            label = ", ".join(
                part
                for part in [
                    row.get("address_one"),
                    row.get("address_two"),
                    row.get("city"),
                    row.get("state"),
                ]
                if part
            )
            subtitle = row.get("near_by")
            score = float(row.get("score") or 0)
            if fuzzy:
                candidates = [
                    label,
                    row.get("city"),
                    row.get("state"),
                    row.get("address_one"),
                    row.get("address_two"),
                    row.get("near_by"),
                ]
                score = self._combine_scores(query_normalized, candidates, score)
            if score < min_score:
                continue
            results.append(
                SearchResult(
                    kind="location",
                    id=row["location_id"],
                    label=label or row["location_id"],
                    subtitle=subtitle,
                    score=score,
                )
            )

        for row in menu_rows:
            subtitle_parts = [row.get("category"), row.get("size")]
            subtitle = " · ".join(part for part in subtitle_parts if part)
            score = float(row.get("score") or 0)
            if fuzzy:
                candidates = [
                    row.get("name"),
                    row.get("category"),
                    row.get("size"),
                ]
                score = self._combine_scores(query_normalized, candidates, score)
            if score < min_score:
                continue
            results.append(
                SearchResult(
                    kind="menu_item",
                    id=row["item_id"],
                    label=row.get("name") or row["item_id"],
                    subtitle=subtitle or None,
                    score=score,
                )
            )

        results.sort(key=lambda item: item.score or 0, reverse=True)
        logger.info("Search query=%s scope=%s results=%s", query, scope, len(results))
        return SearchResponse(query=query, results=results[:limit])

    @staticmethod
    def _combine_scores(query: str, candidates: list[str | None], raw_score: float) -> float:
        if not query:
            return raw_score
        best_similarity = 0.0
        for candidate in candidates:
            if not candidate:
                continue
            candidate_value = str(candidate).strip().lower()
            if not candidate_value:
                continue
            similarity = SequenceMatcher(None, query, candidate_value).ratio()
            if similarity > best_similarity:
                best_similarity = similarity
        normalized = raw_score / 5 if raw_score else 0.0
        combined = max(normalized, best_similarity)
        return round(combined * 5, 3)
