from pydantic_settings import BaseSettings
from pydantic import Field


class MetaSettings(BaseSettings):
    """Meta API configuration - loaded from .env file."""

    # Meta / Facebook
    meta_app_id: str = Field(default="", description="Meta App ID")
    meta_app_secret: str = Field(default="", description="Meta App Secret")
    meta_access_token: str = Field(default="", description="Page Access Token")
    meta_page_id: str = Field(default="", description="Facebook Page ID")

    # Instagram
    instagram_business_account_id: str = Field(default="", description="IG Business Account ID")

    # Image Generation
    image_api_key: str = Field(default="", description="Image generation API key")
    image_api_url: str = Field(default="", description="Image generation API endpoint")

    # General
    debug: bool = False
    log_level: str = "INFO"

    # Meta API
    graph_api_version: str = "v21.0"
    graph_api_base_url: str = "https://graph.facebook.com"

    @property
    def graph_api_url(self) -> str:
        return f"{self.graph_api_base_url}/{self.graph_api_version}"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = MetaSettings()
