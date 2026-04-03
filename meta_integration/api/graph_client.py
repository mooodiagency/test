"""Low-level Meta Graph API client."""

import requests
from typing import Any
from config import settings


class GraphAPIClient:
    """Handles all HTTP communication with the Meta Graph API."""

    def __init__(self, access_token: str | None = None):
        self.access_token = access_token or settings.meta_access_token
        self.base_url = settings.graph_api_url
        self.session = requests.Session()
        self.session.params = {"access_token": self.access_token}

    def get(self, endpoint: str, params: dict | None = None) -> dict[str, Any]:
        """GET request to Graph API."""
        url = f"{self.base_url}/{endpoint}"
        response = self.session.get(url, params=params or {})
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, data: dict | None = None) -> dict[str, Any]:
        """POST request to Graph API."""
        url = f"{self.base_url}/{endpoint}"
        response = self.session.post(url, json=data or {})
        response.raise_for_status()
        return response.json()

    def delete(self, endpoint: str) -> dict[str, Any]:
        """DELETE request to Graph API."""
        url = f"{self.base_url}/{endpoint}"
        response = self.session.delete(url)
        response.raise_for_status()
        return response.json()

    def upload_photo(self, endpoint: str, image_url: str, **kwargs) -> dict[str, Any]:
        """Upload a photo via URL to Graph API."""
        url = f"{self.base_url}/{endpoint}"
        data = {"url": image_url, **kwargs}
        response = self.session.post(url, data=data)
        response.raise_for_status()
        return response.json()

    def verify_token(self) -> dict[str, Any]:
        """Verify the current access token is valid."""
        return self.get("me", params={"fields": "id,name"})
