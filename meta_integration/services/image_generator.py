"""Image Generation service - pluggable backend for generating social media images."""

import httpx
import os
from typing import Any
from config import settings


class ImageGenerator:
    """Generate images for social media posts.

    Supports multiple backends - configure via IMAGE_API_URL and IMAGE_API_KEY.
    Currently set up for HTTP-based image generation APIs (fal.ai, Replicate, etc.)
    """

    def __init__(self):
        self.api_key = settings.image_api_key
        self.api_url = settings.image_api_url
        self.output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "generated_images")
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate(
        self,
        prompt: str,
        width: int = 1080,
        height: int = 1080,
        style: str | None = None,
    ) -> dict[str, Any]:
        """Generate an image from a text prompt.

        Returns dict with 'url' and/or 'local_path' of the generated image.

        Args:
            prompt: Text description of the image to generate
            width: Image width in pixels (default 1080 for Instagram)
            height: Image height in pixels (default 1080 for Instagram)
            style: Optional style modifier (e.g., 'photorealistic', 'illustration')
        """
        full_prompt = prompt
        if style:
            full_prompt = f"{prompt}, {style} style"

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "prompt": full_prompt,
                    "width": width,
                    "height": height,
                },
            )
            response.raise_for_status()
            result = response.json()

        return result

    async def generate_social_image(
        self,
        prompt: str,
        platform: str = "instagram",
    ) -> dict[str, Any]:
        """Generate an image optimized for a specific social platform.

        Automatically sets the right dimensions:
        - Instagram feed: 1080x1080
        - Instagram story: 1080x1920
        - Facebook post: 1200x630
        - Facebook story: 1080x1920
        """
        dimensions = {
            "instagram": (1080, 1080),
            "instagram_story": (1080, 1920),
            "instagram_portrait": (1080, 1350),
            "facebook": (1200, 630),
            "facebook_story": (1080, 1920),
        }

        width, height = dimensions.get(platform, (1080, 1080))
        return await self.generate(prompt, width=width, height=height)
