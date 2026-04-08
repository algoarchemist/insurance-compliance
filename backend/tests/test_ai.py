"""Tests for AI service."""

import pytest
import pytest_asyncio


@pytest.mark.asyncio
async def test_ai_eligibility_chat(client):
    # Get auth token
    init = await client.post("/api/v1/auth/aadhaar/initiate", json={"aadhaar_number": "123456789012"})
    verify = await client.post("/api/v1/auth/aadhaar/verify", json={"txn_id": init.json()["txn_id"], "otp": "123456"})
    token = verify.json()["access_token"]

    response = await client.post(
        "/api/v1/ai/eligibility/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Am I eligible for PMJAY?", "history": []},
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data


@pytest.mark.asyncio
async def test_ai_coverage_summarize(client):
    init = await client.post("/api/v1/auth/aadhaar/initiate", json={"aadhaar_number": "123456789012"})
    verify = await client.post("/api/v1/auth/aadhaar/verify", json={"txn_id": init.json()["txn_id"], "otp": "123456"})
    token = verify.json()["access_token"]

    response = await client.post(
        "/api/v1/ai/coverage/summarize",
        headers={"Authorization": f"Bearer {token}"},
        json={"coverage_grid": {"surgery": "covered", "icu": "covered"}, "language": "en"},
    )
    assert response.status_code == 200
    assert "summary" in response.json()


@pytest.mark.asyncio
async def test_ai_rejection_explain(client):
    init = await client.post("/api/v1/auth/aadhaar/initiate", json={"aadhaar_number": "123456789012"})
    verify = await client.post("/api/v1/auth/aadhaar/verify", json={"txn_id": init.json()["txn_id"], "otp": "123456"})
    token = verify.json()["access_token"]

    response = await client.post(
        "/api/v1/ai/rejection/explain",
        headers={"Authorization": f"Bearer {token}"},
        json={"rejection_code": "NHCX_REJ_001", "claim_id": "test-claim-id", "language": "en"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert "remediation_steps" in data
