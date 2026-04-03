"""MCP Server for Meta Integration.

This server exposes Meta/Facebook/Instagram functionality as tools
that Claude Code can use directly in conversations.

Run with: python -m meta_integration.mcp_server.server
"""

import asyncio
import json
from datetime import datetime
from mcp.server import Server
from mcp.server.stdio import run_server
from mcp.types import Tool, TextContent

from meta_integration.api.facebook import FacebookPageAPI
from meta_integration.api.instagram import InstagramAPI
from meta_integration.services.content_manager import ContentManager
from meta_integration.services.image_generator import ImageGenerator

# Initialize
app = Server("meta-integration")
content_manager = ContentManager()
image_generator = ImageGenerator()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available Meta integration tools."""
    return [
        # ---- Facebook ----
        Tool(
            name="fb_create_post",
            description="Create a text post on the Facebook Page",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "The post text"},
                    "link": {"type": "string", "description": "Optional URL to include"},
                },
                "required": ["message"],
            },
        ),
        Tool(
            name="fb_create_photo_post",
            description="Create a Facebook post with an image",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "The post text"},
                    "image_url": {"type": "string", "description": "Public URL of the image"},
                },
                "required": ["message", "image_url"],
            },
        ),
        Tool(
            name="fb_schedule_post",
            description="Schedule a Facebook post for later publication",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "The post text"},
                    "publish_time": {"type": "string", "description": "ISO datetime for publication (e.g. 2025-01-15T14:00:00)"},
                    "link": {"type": "string", "description": "Optional URL to include"},
                },
                "required": ["message", "publish_time"],
            },
        ),
        Tool(
            name="fb_get_posts",
            description="Get recent posts from the Facebook Page",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of posts to retrieve (default 10)", "default": 10},
                },
            },
        ),
        Tool(
            name="fb_get_page_insights",
            description="Get Facebook Page analytics and insights",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {"type": "string", "enum": ["day", "week", "days_28"], "default": "day"},
                },
            },
        ),
        Tool(
            name="fb_get_scheduled_posts",
            description="Get all scheduled (unpublished) Facebook posts",
            inputSchema={"type": "object", "properties": {}},
        ),
        # ---- Instagram ----
        Tool(
            name="ig_create_post",
            description="Create an Instagram image post (requires image URL)",
            inputSchema={
                "type": "object",
                "properties": {
                    "caption": {"type": "string", "description": "The post caption"},
                    "image_url": {"type": "string", "description": "Public URL of the image"},
                },
                "required": ["caption", "image_url"],
            },
        ),
        Tool(
            name="ig_create_carousel",
            description="Create an Instagram carousel post with multiple images",
            inputSchema={
                "type": "object",
                "properties": {
                    "caption": {"type": "string", "description": "The post caption"},
                    "image_urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of public image URLs (2-10 images)",
                    },
                },
                "required": ["caption", "image_urls"],
            },
        ),
        Tool(
            name="ig_get_media",
            description="Get recent Instagram posts and their metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of posts to retrieve", "default": 10},
                },
            },
        ),
        Tool(
            name="ig_get_insights",
            description="Get Instagram account analytics and insights",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {"type": "string", "enum": ["day", "week", "days_28"], "default": "day"},
                },
            },
        ),
        Tool(
            name="ig_search_hashtag",
            description="Research a hashtag for Instagram - get volume and top posts",
            inputSchema={
                "type": "object",
                "properties": {
                    "hashtag": {"type": "string", "description": "Hashtag to search (without #)"},
                },
                "required": ["hashtag"],
            },
        ),
        # ---- Content Management ----
        Tool(
            name="create_draft",
            description="Create a post draft for review before publishing. Supports Facebook, Instagram, or both.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The post text/caption"},
                    "platform": {"type": "string", "enum": ["facebook", "instagram", "both"], "default": "both"},
                    "image_url": {"type": "string", "description": "Optional image URL"},
                    "hashtags": {"type": "array", "items": {"type": "string"}, "description": "Optional hashtags (without #)"},
                    "scheduled_time": {"type": "string", "description": "Optional ISO datetime for scheduling"},
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="list_drafts",
            description="List all current post drafts awaiting review",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="publish_draft",
            description="Publish an approved draft to its target platform(s)",
            inputSchema={
                "type": "object",
                "properties": {
                    "draft_index": {"type": "integer", "description": "Index of the draft to publish (from list_drafts)"},
                },
                "required": ["draft_index"],
            },
        ),
        # ---- Image Generation ----
        Tool(
            name="generate_image",
            description="Generate an image from a text prompt for social media",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Description of the image to generate"},
                    "platform": {
                        "type": "string",
                        "enum": ["instagram", "instagram_story", "instagram_portrait", "facebook", "facebook_story"],
                        "default": "instagram",
                        "description": "Target platform (sets optimal dimensions)",
                    },
                },
                "required": ["prompt"],
            },
        ),
        # ---- Overview ----
        Tool(
            name="get_overview",
            description="Get a combined overview of both Facebook and Instagram accounts",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        result = await _dispatch_tool(name, arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]


async def _dispatch_tool(name: str, args: dict):
    """Route tool calls to the right handler."""
    fb = FacebookPageAPI()
    ig = InstagramAPI()

    match name:
        # Facebook
        case "fb_create_post":
            return fb.create_post(args["message"], link=args.get("link"))
        case "fb_create_photo_post":
            return fb.create_photo_post(args["message"], args["image_url"])
        case "fb_schedule_post":
            dt = datetime.fromisoformat(args["publish_time"])
            return fb.schedule_post(args["message"], dt, link=args.get("link"))
        case "fb_get_posts":
            return fb.get_posts(limit=args.get("limit", 10))
        case "fb_get_page_insights":
            return fb.get_page_insights(period=args.get("period", "day"))
        case "fb_get_scheduled_posts":
            return fb.get_scheduled_posts()

        # Instagram
        case "ig_create_post":
            return ig.create_image_post(args["image_url"], args["caption"])
        case "ig_create_carousel":
            return ig.create_carousel_post(args["image_urls"], args["caption"])
        case "ig_get_media":
            return ig.get_media(limit=args.get("limit", 10))
        case "ig_get_insights":
            return ig.get_account_insights(period=args.get("period", "day"))
        case "ig_search_hashtag":
            return ig.search_hashtag(args["hashtag"])

        # Content Management
        case "create_draft":
            draft = content_manager.create_draft(
                text=args["text"],
                platform=args.get("platform", "both"),
                image_url=args.get("image_url"),
                hashtags=args.get("hashtags", []),
                scheduled_time=datetime.fromisoformat(args["scheduled_time"]) if args.get("scheduled_time") else None,
            )
            return {"status": "draft_created", "text": draft.text, "platform": draft.platform}
        case "list_drafts":
            drafts = content_manager.list_drafts()
            return [{"index": i, "text": d.text[:100], "platform": d.platform, "status": d.status} for i, d in enumerate(drafts)]
        case "publish_draft":
            return content_manager.publish_draft(args["draft_index"])

        # Image Generation
        case "generate_image":
            return await image_generator.generate_social_image(
                prompt=args["prompt"],
                platform=args.get("platform", "instagram"),
            )

        # Overview
        case "get_overview":
            return content_manager.get_overview()

        case _:
            return {"error": f"Unknown tool: {name}"}


def main():
    """Run the MCP server."""
    asyncio.run(run_server(app))


if __name__ == "__main__":
    main()
