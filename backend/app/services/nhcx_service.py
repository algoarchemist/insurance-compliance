"""NHCX service — full claim lifecycle with sandbox mock fallback."""

import uuid
from datetime import datetime, timezone

import httpx
from config import settings
from app.utils.jwe_utils import encrypt_payload_jwe, build_nhcx_request


async def check_coverage_eligibility(
    policy_id: str, hospital_nhcx_id: str, member_id: str
) -> dict:
    """Check coverage eligibility via NHCX."""
    if not settings.NHCX_AUTH_TOKEN or settings.APP_ENV == "development":
        return {
            "covered": True,
            "empanelment_type": "cashless",
            "tpa_code": "VHTPA",
            "services": {
                "surgery": "covered",
                "icu": "covered",
                "general_ward": "sub_limit:3000",
                "ambulance": "covered",
            },
        }

    api_call_id = str(uuid.uuid4())
    fhir_bundle = {"resourceType": "Bundle", "type": "collection"}  # simplified

    jwe_token = encrypt_payload_jwe(fhir_bundle, settings.NHCX_ENCRYPTION_CERT)
    request_payload = build_nhcx_request(
        fhir_bundle, settings.NHCX_PARTICIPANT_CODE, hospital_nhcx_id, api_call_id
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.NHCX_BASE_URL}/coverageeligibility/check",
            headers={"Authorization": f"Bearer {settings.NHCX_AUTH_TOKEN}"},
            json=request_payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


async def submit_pre_auth(claim_data: dict, fhir_bundle: dict) -> dict:
    """Submit pre-authorization request to NHCX."""
    if not settings.NHCX_AUTH_TOKEN or settings.APP_ENV == "development":
        pre_auth_id = f"PA-{uuid.uuid4().hex[:12]}"
        return {
            "pre_auth_id": pre_auth_id,
            "status": "pre_auth_pending",
            "correlation_id": str(uuid.uuid4()),
        }

    api_call_id = str(uuid.uuid4())
    request_payload = build_nhcx_request(
        fhir_bundle,
        settings.NHCX_PARTICIPANT_CODE,
        claim_data.get("hospital_nhcx_id", ""),
        api_call_id,
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.NHCX_BASE_URL}/preauth/submit",
            headers={"Authorization": f"Bearer {settings.NHCX_AUTH_TOKEN}"},
            json=request_payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


async def poll_pre_auth_status(pre_auth_id: str) -> dict:
    """Poll pre-authorization status from NHCX."""
    if not settings.NHCX_AUTH_TOKEN or settings.APP_ENV == "development":
        return {
            "status": "pre_auth_approved",
            "approved_amount": 80000,
            "notes": "Pre-authorization approved (sandbox)",
        }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.NHCX_BASE_URL}/preauth/status/{pre_auth_id}",
            headers={"Authorization": f"Bearer {settings.NHCX_AUTH_TOKEN}"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


async def submit_claim(fhir_bundle: dict, pre_auth_id: str) -> dict:
    """Submit claim to NHCX."""
    if not settings.NHCX_AUTH_TOKEN or settings.APP_ENV == "development":
        nhcx_claim_id = f"CLM-{uuid.uuid4().hex[:12]}"
        return {
            "nhcx_claim_id": nhcx_claim_id,
            "correlation_id": str(uuid.uuid4()),
            "status": "submitted",
        }

    api_call_id = str(uuid.uuid4())
    request_payload = build_nhcx_request(
        fhir_bundle, settings.NHCX_PARTICIPANT_CODE, "", api_call_id
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.NHCX_BASE_URL}/claim/submit",
            headers={"Authorization": f"Bearer {settings.NHCX_AUTH_TOKEN}"},
            json=request_payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


async def poll_claim_status(nhcx_claim_id: str) -> dict:
    """Poll claim status from NHCX."""
    if not settings.NHCX_AUTH_TOKEN or settings.APP_ENV == "development":
        return {"status": "processing", "approved_amount": None, "notes": "Under review (sandbox)"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.NHCX_BASE_URL}/claim/status/{nhcx_claim_id}",
            headers={"Authorization": f"Bearer {settings.NHCX_AUTH_TOKEN}"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


async def send_communication_response(
    correlation_id: str, response_text: str, docs: list
) -> dict:
    """Respond to TPA query via NHCX communication endpoint."""
    if not settings.NHCX_AUTH_TOKEN or settings.APP_ENV == "development":
        return {"status": "sent", "correlation_id": correlation_id}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.NHCX_BASE_URL}/communication/on-request",
            headers={"Authorization": f"Bearer {settings.NHCX_AUTH_TOKEN}"},
            json={
                "correlationId": correlation_id,
                "response": response_text,
                "documents": docs,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
