import logging

from app.repositories.search import SearchRepository
from app.schemas.search import SearchResponse, SearchResult


logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self, repository: SearchRepository) -> None:
        self._repository = repository

    def search(self, query: str, limit: int, scope: str) -> SearchResponse:
        location_rows = []
        menu_rows = []
        scope_value = scope.lower()
        if scope_value in ("all", "locations"):
            location_rows = self._repository.search_locations(query, limit)
        if scope_value in ("all", "menu"):
            menu_rows = self._repository.search_menu(query, limit)

        results: list[SearchResult] = []
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
            results.append(
                SearchResult(
                    kind="location",
                    id=row["location_id"],
                    label=label or row["location_id"],
                    subtitle=subtitle,
                    score=row.get("score"),
                )
            )

        for row in menu_rows:
            subtitle_parts = [row.get("category"), row.get("size")]
            subtitle = " · ".join(part for part in subtitle_parts if part)
            results.append(
                SearchResult(
                    kind="menu_item",
                    id=row["item_id"],
                    label=row.get("name") or row["item_id"],
                    subtitle=subtitle or None,
                    score=row.get("score"),
                )
            )

        results.sort(key=lambda item: item.score or 0, reverse=True)
        logger.info("Search query=%s scope=%s results=%s", query, scope, len(results))
        return SearchResponse(query=query, results=results[:limit])
