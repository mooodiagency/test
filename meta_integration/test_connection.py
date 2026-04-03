"""Test script to verify Meta API connection and permissions."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from meta_integration.api.graph_client import GraphAPIClient
from meta_integration.api.facebook import FacebookPageAPI
from meta_integration.api.instagram import InstagramAPI


def test_connection():
    """Run connection tests."""
    print("=" * 50)
    print("Meta Integration - Connection Test")
    print("=" * 50)

    # Check config
    print("\n[1] Checking configuration...")
    issues = []
    if not settings.meta_access_token:
        issues.append("META_ACCESS_TOKEN is not set")
    if not settings.meta_page_id:
        issues.append("META_PAGE_ID is not set")
    if not settings.instagram_business_account_id:
        issues.append("INSTAGRAM_BUSINESS_ACCOUNT_ID is not set")

    if issues:
        print("   MISSING CONFIG:")
        for issue in issues:
            print(f"   - {issue}")
        print("\n   Copy .env.example to .env and fill in your credentials.")
        print("   See docs/SETUP_GUIDE.md for instructions.")
        return False

    print("   Config OK")

    # Test Graph API
    print("\n[2] Testing Graph API connection...")
    try:
        client = GraphAPIClient()
        result = client.verify_token()
        print(f"   Connected as: {result.get('name', 'Unknown')}")
    except Exception as e:
        print(f"   FAILED: {e}")
        return False

    # Test Facebook Page
    print("\n[3] Testing Facebook Page access...")
    try:
        fb = FacebookPageAPI()
        page_info = fb.get_page_info()
        print(f"   Page: {page_info.get('name', 'Unknown')}")
        print(f"   Followers: {page_info.get('followers_count', 'N/A')}")
    except Exception as e:
        print(f"   FAILED: {e}")

    # Test Instagram
    print("\n[4] Testing Instagram access...")
    try:
        ig = InstagramAPI()
        account = ig.get_account_info()
        print(f"   Account: @{account.get('username', 'Unknown')}")
        print(f"   Followers: {account.get('followers_count', 'N/A')}")
    except Exception as e:
        print(f"   FAILED: {e}")

    print("\n" + "=" * 50)
    print("Connection test complete!")
    print("=" * 50)
    return True


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
