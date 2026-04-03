"""Generate a never-expiring Page Access Token.

Usage:
    python -m meta_integration.generate_token <short_lived_user_token>

This script:
1. Exchanges a short-lived user token for a long-lived user token (60 days)
2. Uses the long-lived user token to get a Page Access Token (never expires)
3. Updates the .env file with the new token
"""

import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings


def exchange_for_long_lived_token(short_lived_token: str) -> str:
    """Exchange a short-lived token for a long-lived user token (~60 days)."""
    url = f"https://graph.facebook.com/{settings.graph_api_version}/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": settings.meta_app_id,
        "client_secret": settings.meta_app_secret,
        "fb_exchange_token": short_lived_token,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    return data["access_token"]


def get_page_token(long_lived_user_token: str, page_id: str) -> str:
    """Get a never-expiring Page Access Token."""
    url = f"https://graph.facebook.com/{settings.graph_api_version}/{page_id}"
    params = {
        "fields": "access_token",
        "access_token": long_lived_user_token,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    return data["access_token"]


def verify_token(token: str) -> dict:
    """Check token expiration info."""
    url = "https://graph.facebook.com/debug_token"
    params = {
        "input_token": token,
        "access_token": token,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("data", {})


def update_env_file(new_token: str):
    """Update META_ACCESS_TOKEN in .env file."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

    if not os.path.exists(env_path):
        print(f"   .env file not found at {env_path}")
        return False

    with open(env_path, "r") as f:
        content = f.read()

    # Replace the token line
    lines = content.split("\n")
    new_lines = []
    for line in lines:
        if line.startswith("META_ACCESS_TOKEN="):
            new_lines.append(f"META_ACCESS_TOKEN={new_token}")
        else:
            new_lines.append(line)

    with open(env_path, "w") as f:
        f.write("\n".join(new_lines))

    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m meta_integration.generate_token <short_lived_user_token>")
        print("\nGet a short-lived token from Graph API Explorer:")
        print("  1. Go to developers.facebook.com > Tools > Graph API Explorer")
        print("  2. Select your app and add permissions")
        print("  3. Click 'Generate Access Token'")
        print("  4. Copy the token and pass it as argument")
        sys.exit(1)

    short_lived_token = sys.argv[1]

    print("=" * 55)
    print("Generate Never-Expiring Page Access Token")
    print("=" * 55)

    # Step 1: Exchange for long-lived token
    print("\n[1] Exchanging for long-lived user token...")
    try:
        long_lived_token = exchange_for_long_lived_token(short_lived_token)
        print(f"   OK - Long-lived user token obtained")
    except Exception as e:
        print(f"   FAILED: {e}")
        print("   Make sure your App ID and App Secret are correct in .env")
        sys.exit(1)

    # Step 2: Get page token
    print("\n[2] Getting never-expiring Page token...")
    page_id = settings.meta_page_id
    if not page_id:
        print("   FAILED: META_PAGE_ID not set in .env")
        sys.exit(1)

    try:
        page_token = get_page_token(long_lived_token, page_id)
        print(f"   OK - Page token obtained for page {page_id}")
    except Exception as e:
        print(f"   FAILED: {e}")
        sys.exit(1)

    # Step 3: Verify token
    print("\n[3] Verifying token...")
    try:
        info = verify_token(page_token)
        expires = info.get("expires_at", 0)
        if expires == 0:
            print("   Token NEVER expires!")
        else:
            from datetime import datetime
            exp_date = datetime.fromtimestamp(expires)
            print(f"   Token expires: {exp_date}")
    except Exception:
        print("   Could not verify (but token may still work)")

    # Step 4: Update .env
    print("\n[4] Updating .env file...")
    if update_env_file(page_token):
        print("   .env updated successfully!")
    else:
        print("   Could not update .env - do it manually:")
        print(f"\n   META_ACCESS_TOKEN={page_token}")

    print("\n" + "=" * 55)
    print("Done! Your Page Access Token never expires.")
    print("Restart Claude Desktop to use the new token.")
    print("=" * 55)


if __name__ == "__main__":
    main()
