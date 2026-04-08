"""Tests for claims endpoints."""

import pytest
import pytest_asyncio


async def _get_auth_token(client):
    """Helper to get auth token."""
    init = await client.post(
        "/api/v1/auth/aadhaar/initiate",
        json={"aadhaar_number": "123456789012"},
    )
    verify = await client.post(
        "/api/v1/auth/aadhaar/verify",
        json={"txn_id": init.json()["txn_id"], "otp": "123456"},
    )
    return verify.json()["access_token"]


@pytest.mark.asyncio
async def test_list_claims_unauthorized(client):
    response = await client.get("/api/v1/claims")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_claims_empty(client):
    token = await _get_auth_token(client)
    response = await client.get(
        "/api/v1/claims",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_policies_empty(client):
    token = await _get_auth_token(client)
    response = await client.get(
        "/api/v1/policies",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["active_count"] == 0


@pytest.mark.asyncio
async def test_pmjay_check(client):
    token = await _get_auth_token(client)
    response = await client.post(
        "/api/v1/policies/pmjay/check",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "eligible" in data
