import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_update_user_bio_success(async_client: AsyncClient, admin_user, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    updated_data = {"bio": "Updated bio for professional user"}
    response = await async_client.put(f"/users/{admin_user.id}", json=updated_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["bio"] == updated_data["bio"]

@pytest.mark.asyncio
async def test_update_user_linkedin_success(async_client: AsyncClient, admin_user, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    updated_data = {"linkedin_profile_url": "https://linkedin.com/in/updated-profile"}
    response = await async_client.put(f"/users/{admin_user.id}", json=updated_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["linkedin_profile_url"] == updated_data["linkedin_profile_url"]

@pytest.mark.asyncio
async def test_update_user_github_success(async_client: AsyncClient, admin_user, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    updated_data = {"github_profile_url": "https://github.com/updated-profile"}
    response = await async_client.put(f"/users/{admin_user.id}", json=updated_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["github_profile_url"] == updated_data["github_profile_url"]

@pytest.mark.asyncio
async def test_update_user_invalid_url(async_client: AsyncClient, admin_user, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    invalid_data = {"linkedin_profile_url": "invalid-url"}
    response = await async_client.put(f"/users/{admin_user.id}", json=invalid_data, headers=headers)
    assert response.status_code == 422
    assert "Invalid URL format" in response.text

@pytest.mark.asyncio
async def test_update_user_attempt_update_forbidden_fields(async_client: AsyncClient, admin_user, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    update_attempt = {
        "bio": "Trying valid update",
        "is_professional": True,
        "email_verified": True
    }
    response = await async_client.put(f"/users/{admin_user.id}", json=update_attempt, headers=headers)
    assert response.status_code == 200
    # Forbidden fields should remain unchanged
    assert response.json()["bio"] == "Trying valid update"
    assert response.json()["is_professional"] is False  # Still default value

