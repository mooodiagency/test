"""Facebook Page API - posts, scheduling, and page management."""

from datetime import datetime
from typing import Any
from meta_integration.api.graph_client import GraphAPIClient
from config import settings


class FacebookPageAPI:
    """Manage Facebook Page posts and content."""

    def __init__(self, client: GraphAPIClient | None = None):
        self.client = client or GraphAPIClient()
        self.page_id = settings.meta_page_id

    # ---- Posts ----

    def create_post(self, message: str, link: str | None = None) -> dict[str, Any]:
        """Create a new post on the Facebook Page."""
        data = {"message": message}
        if link:
            data["link"] = link
        return self.client.post(f"{self.page_id}/feed", data=data)

    def create_photo_post(
        self, message: str, image_url: str
    ) -> dict[str, Any]:
        """Create a post with a photo (via URL)."""
        return self.client.upload_photo(
            f"{self.page_id}/photos",
            image_url=image_url,
            message=message,
        )

    def schedule_post(
        self, message: str, publish_time: datetime, link: str | None = None
    ) -> dict[str, Any]:
        """Schedule a post for future publication.

        publish_time must be between 10 minutes and 75 days from now.
        """
        data = {
            "message": message,
            "published": False,
            "scheduled_publish_time": int(publish_time.timestamp()),
        }
        if link:
            data["link"] = link
        return self.client.post(f"{self.page_id}/feed", data=data)

    def get_scheduled_posts(self) -> list[dict[str, Any]]:
        """Get all scheduled (unpublished) posts."""
        result = self.client.get(
            f"{self.page_id}/scheduled_posts",
            params={"fields": "message,scheduled_publish_time,created_time"},
        )
        return result.get("data", [])

    # ---- Read ----

    def get_posts(self, limit: int = 25) -> list[dict[str, Any]]:
        """Get recent posts from the page."""
        result = self.client.get(
            f"{self.page_id}/posts",
            params={
                "fields": "message,created_time,shares,permalink_url",
                "limit": limit,
            },
        )
        return result.get("data", [])

    def get_post_insights(self, post_id: str) -> dict[str, Any]:
        """Get engagement metrics for a specific post."""
        result = self.client.get(
            f"{post_id}/insights",
            params={
                "metric": "post_impressions,post_engaged_users,post_reactions_by_type_total"
            },
        )
        return result.get("data", [])

    # ---- Page Insights ----

    def get_page_insights(
        self, period: str = "day", days: int = 7
    ) -> dict[str, Any]:
        """Get page-level analytics.

        period: 'day', 'week', 'days_28'
        """
        result = self.client.get(
            f"{self.page_id}/insights",
            params={
                "metric": "page_impressions,page_engaged_users,page_fan_adds,page_views_total",
                "period": period,
            },
        )
        return result.get("data", [])

    def get_page_info(self) -> dict[str, Any]:
        """Get basic page information."""
        return self.client.get(
            self.page_id,
            params={"fields": "name,fan_count,followers_count,about,category"},
        )

    # ---- Manage ----

    def delete_post(self, post_id: str) -> dict[str, Any]:
        """Delete a post."""
        return self.client.delete(post_id)

    def update_post(self, post_id: str, message: str) -> dict[str, Any]:
        """Update an existing post's message."""
        return self.client.post(post_id, data={"message": message})
