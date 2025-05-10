import pytest

@pytest.mark.asyncio
async def test_register_fails_with_short_password(async_client):
    user_data = {
        "email": "shortpass@example.com",
        "nickname": "shorty",
        "first_name": "Test",
        "last_name": "User",
        "role": "ANONYMOUS",
        "password": "Short1!"
    }
    response = await async_client.post("/register/", json=user_data)
    assert response.status_code == 422
    assert "Password must be at least 8 characters long" in response.text

@pytest.mark.asyncio
async def test_register_fails_missing_special_char(async_client):
    user_data = {
        "email": "nospecial@example.com",
        "nickname": "nospecial",
        "first_name": "Test",
        "last_name": "User",
        "role": "ANONYMOUS",
        "password": "ValidPass123"
    }
    response = await async_client.post("/register/", json=user_data)
    assert response.status_code == 422
    assert "Password must include at least one special character" in response.text

@pytest.mark.asyncio
async def test_register_success_with_strong_password(async_client):
    user_data = {
        "email": "strong@example.com",
        "nickname": "strongnick",
        "first_name": "Test",
        "last_name": "User",
        "role": "ANONYMOUS",
        "password": "StrongPass#123"
    }
    response = await async_client.post("/register/", json=user_data)
    assert response.status_code in [200, 201]
    assert response.json()["email"] == "strong@example.com"
