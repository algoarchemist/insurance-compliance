"""Tests for auth endpoints."""

import pytest
import pytest_asyncio


@pytest.mark.asyncio
async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "Sugamai"
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_aadhaar_initiate(client):
    response = await client.post(
        "/api/v1/auth/aadhaar/initiate",
        json={"aadhaar_number": "123456789012"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "txn_id" in data
    assert "message" in data


@pytest.mark.asyncio
async def test_aadhaar_verify(client):
    # First initiate
    init_resp = await client.post(
        "/api/v1/auth/aadhaar/initiate",
        json={"aadhaar_number": "123456789012"},
    )
    txn_id = init_resp.json()["txn_id"]

    # Then verify
    verify_resp = await client.post(
        "/api/v1/auth/aadhaar/verify",
        json={"txn_id": txn_id, "otp": "123456"},
    )
    assert verify_resp.status_code == 200
    data = verify_resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "user" in data


@pytest.mark.asyncio
async def test_aadhaar_invalid_number(client):
    response = await client.post(
        "/api/v1/auth/aadhaar/initiate",
        json={"aadhaar_number": "12345"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_refresh_token(client):
    # Get tokens
    init = await client.post(
        "/api/v1/auth/aadhaar/initiate",
        json={"aadhaar_number": "123456789012"},
    )
    verify = await client.post(
        "/api/v1/auth/aadhaar/verify",
        json={"txn_id": init.json()["txn_id"], "otp": "123456"},
    )
    refresh_token = verify.json()["refresh_token"]

    # Refresh
    refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh.status_code == 200
    assert "access_token" in refresh.json()
