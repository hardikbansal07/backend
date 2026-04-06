"""
Unit tests for Facebook OAuth authentication.
All Facebook Graph API calls are mocked using httpx.

Tests:
1. Valid token → user created successfully
2. Invalid/expired token → 401 Unauthorized
3. Token with no email → creates user with fallback email
4. Same FB user logs in twice → no duplicate created
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---- Mock Data ----

MOCK_DEBUG_TOKEN_VALID = {
    "data": {
        "app_id": "123456789",
        "is_valid": True,
        "user_id": "fb_user_001",
        "scopes": ["email", "public_profile"]
    }
}

MOCK_DEBUG_TOKEN_INVALID = {
    "data": {
        "is_valid": False,
        "error": {"message": "Token expired"}
    }
}

MOCK_FB_USER_WITH_EMAIL = {
    "id": "fb_user_001",
    "name": "Rahul Sharma",
    "email": "rahul@example.com",
    "picture": {
        "data": {
            "url": "https://graph.facebook.com/fb_user_001/picture?type=large"
        }
    }
}

MOCK_FB_USER_NO_EMAIL = {
    "id": "fb_user_002",
    "name": "Anonymous User",
    "picture": {
        "data": {
            "url": "https://graph.facebook.com/fb_user_002/picture?type=large"
        }
    }
}


# ---- Helper: Mock httpx responses ----

def make_mock_response(json_data: dict, status_code: int = 200):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.text = str(json_data)
    return mock


# ---- Tests ----

class TestVerifyFacebookToken:

    @pytest.mark.asyncio
    async def test_valid_token_returns_user_info(self):
        """A valid Facebook token should return user profile data."""
        with patch("auth.FACEBOOK_APP_ID", "123456789"), \
             patch("auth.FACEBOOK_APP_SECRET", "test_secret"), \
             patch("httpx.AsyncClient") as mock_client_cls:

            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            # Mock /debug_token → valid
            # Mock /me → user info
            mock_client.get.side_effect = [
                make_mock_response(MOCK_DEBUG_TOKEN_VALID),
                make_mock_response(MOCK_FB_USER_WITH_EMAIL),
            ]

            from auth import verify_facebook_token
            result = await verify_facebook_token("valid_token_abc")

            assert result["id"] == "fb_user_001"
            assert result["email"] == "rahul@example.com"
            assert result["name"] == "Rahul Sharma"

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self):
        """An invalid or expired Facebook token should raise HTTP 401."""
        with patch("auth.FACEBOOK_APP_ID", "123456789"), \
             patch("auth.FACEBOOK_APP_SECRET", "test_secret"), \
             patch("httpx.AsyncClient") as mock_client_cls:

            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            # Mock /debug_token → invalid
            mock_client.get.return_value = make_mock_response(MOCK_DEBUG_TOKEN_INVALID)

            from auth import verify_facebook_token

            with pytest.raises(HTTPException) as exc_info:
                await verify_facebook_token("fake_expired_token")

            assert exc_info.value.status_code == 401
            assert "invalid" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_token_wrong_app_raises_401(self):
        """A token from a different app should be rejected."""
        debug_response = {
            "data": {
                "app_id": "999999999",  # Different app ID!
                "is_valid": True,
            }
        }
        with patch("auth.FACEBOOK_APP_ID", "123456789"), \
             patch("auth.FACEBOOK_APP_SECRET", "test_secret"), \
             patch("httpx.AsyncClient") as mock_client_cls:

            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = make_mock_response(debug_response)

            from auth import verify_facebook_token

            with pytest.raises(HTTPException) as exc_info:
                await verify_facebook_token("other_app_token")

            assert exc_info.value.status_code == 401


class TestGetOrCreateFacebookUser:

    @pytest.mark.asyncio
    async def test_new_user_with_email_is_created(self):
        """A new Facebook user with email should be created once."""
        mock_db = MagicMock()
        mock_db.users.find_one = AsyncMock(return_value=None)  # No existing user
        mock_db.users.insert_one = AsyncMock()

        with patch("auth.mongo_db") as mock_mongo:
            mock_mongo.db = mock_db

            from auth import get_or_create_facebook_user
            user = await get_or_create_facebook_user(MOCK_FB_USER_WITH_EMAIL)

            # Assert insert was called exactly once
            mock_db.users.insert_one.assert_called_once()
            assert user.email == "rahul@example.com"
            assert user.facebook_id == "fb_user_001"
            assert user.auth_provider == "facebook"
            assert user.profile_photo is not None

    @pytest.mark.asyncio
    async def test_no_duplicate_on_second_login(self):
        """The same Facebook user logging in twice should NOT create a second account."""
        existing_doc = {
            "email": "rahul@example.com",
            "username": "Rahul Sharma",
            "full_name": "Rahul Sharma",
            "hashed_password": "",
            "facebook_id": "fb_user_001",
            "auth_provider": "facebook",
            "profile_photo": "https://example.com/photo.jpg",
            "disabled": False,
            "credits": 5.0,
            "is_guest": False,
            "preferred_language": "English",
            "role": "user",
        }

        mock_db = MagicMock()
        # First find_one (by facebook_id) returns existing user
        mock_db.users.find_one = AsyncMock(side_effect=[existing_doc, existing_doc])
        mock_db.users.update_one = AsyncMock()
        mock_db.users.insert_one = AsyncMock()

        with patch("auth.mongo_db") as mock_mongo:
            mock_mongo.db = mock_db

            from auth import get_or_create_facebook_user
            user = await get_or_create_facebook_user(MOCK_FB_USER_WITH_EMAIL)

            # insert_one should NOT be called — user already exists
            mock_db.users.insert_one.assert_not_called()
            # update_one should be called to refresh last_active
            mock_db.users.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_without_email_gets_fallback(self):
        """A Facebook user with no email should get a stable fallback email."""
        mock_db = MagicMock()
        mock_db.users.find_one = AsyncMock(return_value=None)
        mock_db.users.insert_one = AsyncMock()

        with patch("auth.mongo_db") as mock_mongo:
            mock_mongo.db = mock_db

            from auth import get_or_create_facebook_user
            user = await get_or_create_facebook_user(MOCK_FB_USER_NO_EMAIL)

            # Should use stable fallback email, not id@facebook.user
            assert "facebook.user" not in user.email
            assert "fb_user_002" in user.email
            assert user.facebook_id == "fb_user_002"
            assert user.auth_provider == "facebook"
