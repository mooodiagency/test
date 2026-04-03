"""MCP Server for Meta Integration.

This server exposes Meta/Facebook/Instagram functionality as tools
that Claude Code can use directly in conversations.

Run with: python -m meta_integration.mcp_server.server
"""

import asyncio
import json
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from mcp.types import Tool, TextContent

from meta_integration.api.facebook import FacebookPageAPI
from meta_integration.api.instagram import InstagramAPI
from meta_integration.services.content_manager import ContentManager
from meta_integration.services.image_generator import ImageGenerator

# Initialize
mcp = FastMCP("meta-integration")
content_manager = ContentManager()
image_generator = ImageGenerator()


# ---- Facebook Tools ----

@mcp.tool()
def fb_create_post(message: str, link: str | None = None) -> str:
    """Create a text post on the Facebook Page."""
    fb = FacebookPageAPI()
    result = fb.create_post(message, link=link)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def fb_create_photo_post(message: str, image_url: str) -> str:
    """Create a Facebook post with an image."""
    fb = FacebookPageAPI()
    result = fb.create_photo_post(message, image_url)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def fb_schedule_post(message: str, publish_time: str, link: str | None = None) -> str:
    """Schedule a Facebook post for later publication. publish_time is ISO datetime e.g. 2025-01-15T14:00:00."""
    fb = FacebookPageAPI()
    dt = datetime.fromisoformat(publish_time)
    result = fb.schedule_post(message, dt, link=link)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def fb_get_posts(limit: int = 10) -> str:
    """Get recent posts from the Facebook Page."""
    fb = FacebookPageAPI()
    result = fb.get_posts(limit=limit)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def fb_get_page_insights(period: str = "day") -> str:
    """Get Facebook Page analytics and insights. period: day, week, or days_28."""
    fb = FacebookPageAPI()
    result = fb.get_page_insights(period=period)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def fb_get_scheduled_posts() -> str:
    """Get all scheduled (unpublished) Facebook posts."""
    fb = FacebookPageAPI()
    result = fb.get_scheduled_posts()
    return json.dumps(result, indent=2, default=str)


# ---- Instagram Tools ----

@mcp.tool()
def ig_create_post(caption: str, image_url: str) -> str:
    """Create an Instagram image post (requires a public image URL)."""
    ig = InstagramAPI()
    result = ig.create_image_post(image_url, caption)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def ig_create_carousel(caption: str, image_urls: list[str]) -> str:
    """Create an Instagram carousel post with multiple images (2-10 public URLs)."""
    ig = InstagramAPI()
    result = ig.create_carousel_post(image_urls, caption)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def ig_get_media(limit: int = 10) -> str:
    """Get recent Instagram posts and their metrics."""
    ig = InstagramAPI()
    result = ig.get_media(limit=limit)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def ig_get_insights(period: str = "day") -> str:
    """Get Instagram account analytics. period: day, week, or days_28."""
    ig = InstagramAPI()
    result = ig.get_account_insights(period=period)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def ig_search_hashtag(hashtag: str) -> str:
    """Research a hashtag for Instagram - get volume and top posts."""
    ig = InstagramAPI()
    result = ig.search_hashtag(hashtag)
    return json.dumps(result, indent=2, default=str)


# ---- Content Management Tools ----

@mcp.tool()
def create_draft(text: str, platform: str = "facebook", image_url: str | None = None, hashtags: list[str] | None = None, scheduled_time: str | None = None) -> str:
    """Create a post draft for review before publishing. platform: facebook, instagram, or both."""
    draft = content_manager.create_draft(
        text=text,
        platform=platform,
        image_url=image_url,
        hashtags=hashtags or [],
        scheduled_time=datetime.fromisoformat(scheduled_time) if scheduled_time else None,
    )
    return json.dumps({"status": "draft_created", "text": draft.text, "platform": draft.platform}, indent=2)


@mcp.tool()
def list_drafts() -> str:
    """List all current post drafts awaiting review."""
    drafts = content_manager.list_drafts()
    result = [{"index": i, "text": d.text[:100], "platform": d.platform, "status": d.status} for i, d in enumerate(drafts)]
    return json.dumps(result, indent=2)


@mcp.tool()
def publish_draft(draft_index: int) -> str:
    """Publish an approved draft to its target platform(s)."""
    result = content_manager.publish_draft(draft_index)
    return json.dumps(result, indent=2, default=str)


# ---- Overview ----

@mcp.tool()
def get_overview() -> str:
    """Get a combined overview of Facebook and Instagram accounts."""
    result = content_manager.get_overview()
    return json.dumps(result, indent=2, default=str)


def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
