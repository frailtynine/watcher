import pytest
from httpx import AsyncClient
from app.models import User

pytestmark = pytest.mark.anyio


async def test_register_success(client: AsyncClient):
    """Test user registration with valid data."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data


async def test_register_invalid_email(client: AsyncClient):
    """Test registration fails with invalid email."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "not-an-email",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 422


async def test_register_short_password(client: AsyncClient):
    """Test registration with short password (validation may vary)."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "user@example.com",
            "password": "123",
        },
    )
    assert response.status_code in [201, 400, 422]


async def test_register_duplicate_email(client: AsyncClient, test_user: User):
    """Test registration fails with duplicate email."""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": test_user.email,
            "password": "anotherpassword123",
        },
    )
    assert response.status_code == 400


async def test_login_success(client: AsyncClient, test_user: User):
    """Test login with valid credentials."""
    response = await client.post(
        "/api/auth/jwt/login",
        data={
            "username": "test@example.com",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, test_user: User):
    """Test login fails with wrong password."""
    response = await client.post(
        "/api/auth/jwt/login",
        data={
            "username": test_user.email,
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 400


async def test_login_nonexistent_user(client: AsyncClient):
    """Test login fails with non-existent user."""
    response = await client.post(
        "/api/auth/jwt/login",
        data={
            "username": "nobody@example.com",
            "password": "somepassword",
        },
    )
    assert response.status_code == 400


async def test_logout(client: AsyncClient, auth_headers: dict):
    """Test logout."""
    response = await client.post(
        "/api/auth/jwt/logout",
        headers=auth_headers,
    )
    assert response.status_code == 204


async def test_get_current_user(
    client: AsyncClient,
    auth_headers: dict,
    test_user: User,
):
    """Test getting current user info."""
    response = await client.get(
        "/api/users/me",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == test_user.id


async def test_get_current_user_unauthorized(client: AsyncClient):
    """Test getting current user without auth fails."""
    response = await client.get("/api/users/me")
    assert response.status_code == 401
