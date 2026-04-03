"""Content Manager - orchestrates content creation and publishing."""

from datetime import datetime
from dataclasses import dataclass, field
from typing import Any
from meta_integration.api.facebook import FacebookPageAPI
from meta_integration.api.instagram import InstagramAPI


@dataclass
class PostDraft:
    """A draft post ready for review before publishing."""

    text: str
    platform: str  # "facebook", "instagram", "both"
    image_url: str | None = None
    image_urls: list[str] = field(default_factory=list)
    link: str | None = None
    hashtags: list[str] = field(default_factory=list)
    scheduled_time: datetime | None = None
    status: str = "draft"  # draft, approved, published, failed

    @property
    def full_text(self) -> str:
        """Text with hashtags appended."""
        if self.hashtags:
            tags = " ".join(f"#{tag}" for tag in self.hashtags)
            return f"{self.text}\n\n{tags}"
        return self.text


class ContentManager:
    """Manages the content pipeline: draft -> review -> publish."""

    def __init__(self):
        self.facebook = FacebookPageAPI()
        self.instagram = InstagramAPI()
        self.drafts: list[PostDraft] = []

    def create_draft(
        self,
        text: str,
        platform: str = "both",
        image_url: str | None = None,
        hashtags: list[str] | None = None,
        scheduled_time: datetime | None = None,
        link: str | None = None,
    ) -> PostDraft:
        """Create a new post draft for review."""
        draft = PostDraft(
            text=text,
            platform=platform,
            image_url=image_url,
            hashtags=hashtags or [],
            scheduled_time=scheduled_time,
            link=link,
        )
        self.drafts.append(draft)
        return draft

    def list_drafts(self) -> list[PostDraft]:
        """List all current drafts."""
        return [d for d in self.drafts if d.status == "draft"]

    def publish_draft(self, draft_index: int) -> dict[str, Any]:
        """Publish an approved draft to the selected platform(s)."""
        draft = self.drafts[draft_index]
        results = {}

        if draft.platform in ("facebook", "both"):
            results["facebook"] = self._publish_to_facebook(draft)

        if draft.platform in ("instagram", "both"):
            results["instagram"] = self._publish_to_instagram(draft)

        draft.status = "published"
        return results

    def _publish_to_facebook(self, draft: PostDraft) -> dict[str, Any]:
        """Publish a draft to Facebook."""
        text = draft.full_text

        if draft.scheduled_time:
            return self.facebook.schedule_post(text, draft.scheduled_time, link=draft.link)
        elif draft.image_url:
            return self.facebook.create_photo_post(text, draft.image_url)
        else:
            return self.facebook.create_post(text, link=draft.link)

    def _publish_to_instagram(self, draft: PostDraft) -> dict[str, Any]:
        """Publish a draft to Instagram."""
        text = draft.full_text

        if draft.image_urls and len(draft.image_urls) > 1:
            return self.instagram.create_carousel_post(draft.image_urls, text)
        elif draft.image_url:
            return self.instagram.create_image_post(draft.image_url, text)
        else:
            # Instagram requires an image - cannot post text only
            raise ValueError("Instagram posts require at least one image.")

    # ---- Analytics shortcuts ----

    def get_overview(self) -> dict[str, Any]:
        """Get a combined overview of both platforms."""
        return {
            "facebook": {
                "page_info": self.facebook.get_page_info(),
                "recent_posts": self.facebook.get_posts(limit=5),
            },
            "instagram": {
                "account_info": self.instagram.get_account_info(),
                "recent_media": self.instagram.get_media(limit=5),
            },
        }
