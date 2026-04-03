"""Instagram Business API - posts, stories, and insights."""

from typing import Any
from meta_integration.api.graph_client import GraphAPIClient
from config import settings


class InstagramAPI:
    """Manage Instagram Business account content and insights."""

    def __init__(self, client: GraphAPIClient | None = None):
        self.client = client or GraphAPIClient()
        self.ig_account_id = settings.instagram_business_account_id

    # ---- Publishing (2-step process) ----

    def create_image_post(self, image_url: str, caption: str) -> dict[str, Any]:
        """Create an Instagram image post (2-step: create container, then publish).

        image_url must be a publicly accessible URL.
        """
        # Step 1: Create media container
        container = self.client.post(
            f"{self.ig_account_id}/media",
            data={"image_url": image_url, "caption": caption},
        )
        container_id = container["id"]

        # Step 2: Publish the container
        return self.client.post(
            f"{self.ig_account_id}/media_publish",
            data={"creation_id": container_id},
        )

    def create_carousel_post(
        self, image_urls: list[str], caption: str
    ) -> dict[str, Any]:
        """Create a carousel post with multiple images."""
        # Step 1: Create individual media containers
        children_ids = []
        for url in image_urls:
            container = self.client.post(
                f"{self.ig_account_id}/media",
                data={"image_url": url, "is_carousel_item": True},
            )
            children_ids.append(container["id"])

        # Step 2: Create carousel container
        carousel = self.client.post(
            f"{self.ig_account_id}/media",
            data={
                "media_type": "CAROUSEL",
                "children": ",".join(children_ids),
                "caption": caption,
            },
        )

        # Step 3: Publish
        return self.client.post(
            f"{self.ig_account_id}/media_publish",
            data={"creation_id": carousel["id"]},
        )

    def create_reel(
        self, video_url: str, caption: str, share_to_feed: bool = True
    ) -> dict[str, Any]:
        """Create an Instagram Reel."""
        container = self.client.post(
            f"{self.ig_account_id}/media",
            data={
                "video_url": video_url,
                "caption": caption,
                "media_type": "REELS",
                "share_to_feed": share_to_feed,
            },
        )
        return self.client.post(
            f"{self.ig_account_id}/media_publish",
            data={"creation_id": container["id"]},
        )

    # ---- Read ----

    def get_media(self, limit: int = 25) -> list[dict[str, Any]]:
        """Get recent media from the Instagram account."""
        result = self.client.get(
            f"{self.ig_account_id}/media",
            params={
                "fields": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count",
                "limit": limit,
            },
        )
        return result.get("data", [])

    def get_media_insights(self, media_id: str) -> list[dict[str, Any]]:
        """Get insights for a specific media item."""
        result = self.client.get(
            f"{media_id}/insights",
            params={"metric": "impressions,reach,engagement,saved"},
        )
        return result.get("data", [])

    # ---- Account Insights ----

    def get_account_insights(self, period: str = "day") -> list[dict[str, Any]]:
        """Get account-level insights.

        period: 'day', 'week', 'days_28', 'lifetime'
        """
        result = self.client.get(
            f"{self.ig_account_id}/insights",
            params={
                "metric": "impressions,reach,follower_count,profile_views",
                "period": period,
            },
        )
        return result.get("data", [])

    def get_account_info(self) -> dict[str, Any]:
        """Get basic account information."""
        return self.client.get(
            self.ig_account_id,
            params={
                "fields": "name,username,biography,followers_count,follows_count,media_count,profile_picture_url"
            },
        )

    # ---- Hashtag Research ----

    def search_hashtag(self, hashtag_name: str) -> dict[str, Any]:
        """Search for a hashtag ID."""
        result = self.client.get(
            "ig_hashtag_search",
            params={"q": hashtag_name, "user_id": self.ig_account_id},
        )
        return result.get("data", [])

    def get_hashtag_top_media(self, hashtag_id: str) -> list[dict[str, Any]]:
        """Get top media for a hashtag."""
        result = self.client.get(
            f"{hashtag_id}/top_media",
            params={
                "user_id": self.ig_account_id,
                "fields": "id,caption,media_type,like_count,comments_count,permalink",
            },
        )
        return result.get("data", [])
