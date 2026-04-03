"""Analytics service - read and analyze Meta data."""

from typing import Any
import json
import os
from datetime import datetime
from meta_integration.api.facebook import FacebookPageAPI
from meta_integration.api.instagram import InstagramAPI


class AnalyticsService:
    """Read, analyze, and export Meta analytics data."""

    def __init__(self):
        self.facebook = FacebookPageAPI()
        self.instagram = InstagramAPI()
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
        os.makedirs(self.data_dir, exist_ok=True)

    # ---- Combined Reports ----

    def get_full_report(self) -> dict[str, Any]:
        """Generate a full analytics report for both platforms."""
        return {
            "generated_at": datetime.now().isoformat(),
            "facebook": {
                "page_info": self.facebook.get_page_info(),
                "insights": self.facebook.get_page_insights(period="day"),
                "recent_posts": self._enrich_fb_posts(self.facebook.get_posts(limit=10)),
            },
            "instagram": {
                "account_info": self.instagram.get_account_info(),
                "insights": self.instagram.get_account_insights(period="day"),
                "recent_media": self.instagram.get_media(limit=10),
            },
        }

    def _enrich_fb_posts(self, posts: list[dict]) -> list[dict]:
        """Add insights to each Facebook post."""
        enriched = []
        for post in posts:
            try:
                insights = self.facebook.get_post_insights(post["id"])
                post["insights"] = insights
            except Exception:
                post["insights"] = None
            enriched.append(post)
        return enriched

    # ---- Export ----

    def export_report(self, filename: str | None = None) -> str:
        """Export a full report to JSON file."""
        report = self.get_full_report()
        if not filename:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, default=str)
        return filepath

    def export_posts_csv(self, platform: str = "both") -> str:
        """Export posts data as CSV for further analysis."""
        import csv

        filename = f"posts_{platform}_{datetime.now().strftime('%Y%m%d')}.csv"
        filepath = os.path.join(self.data_dir, filename)

        rows = []
        if platform in ("facebook", "both"):
            for post in self.facebook.get_posts(limit=50):
                rows.append({
                    "platform": "facebook",
                    "id": post.get("id"),
                    "message": post.get("message", "")[:200],
                    "created_time": post.get("created_time"),
                    "permalink": post.get("permalink_url"),
                })

        if platform in ("instagram", "both"):
            for media in self.instagram.get_media(limit=50):
                rows.append({
                    "platform": "instagram",
                    "id": media.get("id"),
                    "message": media.get("caption", "")[:200],
                    "created_time": media.get("timestamp"),
                    "permalink": media.get("permalink"),
                })

        if rows:
            with open(filepath, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        return filepath

    # ---- Competitive / Hashtag Research ----

    def research_hashtags(self, hashtags: list[str]) -> list[dict[str, Any]]:
        """Research multiple hashtags and return their top posts."""
        results = []
        for tag in hashtags:
            search = self.instagram.search_hashtag(tag)
            if search:
                hashtag_id = search[0]["id"]
                top_media = self.instagram.get_hashtag_top_media(hashtag_id)
                results.append({
                    "hashtag": tag,
                    "id": hashtag_id,
                    "top_posts": top_media[:5],
                })
        return results
