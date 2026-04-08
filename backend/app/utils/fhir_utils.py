"""FHIR R4 helper utilities."""

from datetime import datetime, timezone


def create_patient_resource(user: dict) -> dict:
    """Create a FHIR Patient resource from user data."""
    return {
        "resourceType": "Patient",
        "id": str(user.get("id", "")),
        "name": [{"text": user.get("full_name", ""), "use": "official"}],
        "birthDate": str(user.get("date_of_birth", "")),
        "gender": _fhir_gender(user.get("gender", "")),
        "telecom": [{"system": "phone", "value": user.get("phone", "")}],
        "identifier": [
            {"system": "https://ndhm.gov.in/patients", "value": user.get("abha_number", "")},
            {"system": "https://sugamai.in/swasthid", "value": user.get("swasth_id", "")},
        ],
        "address": [
            {
                "state": user.get("state", ""),
                "district": user.get("district", ""),
            }
        ],
    }


def create_organization_resource(hospital: dict) -> dict:
    """Create a FHIR Organization resource from hospital data."""
    return {
        "resourceType": "Organization",
        "id": str(hospital.get("id", "")),
        "name": hospital.get("name", ""),
        "identifier": [
            {"system": "https://hcx.org/participants", "value": hospital.get("nhcx_provider_id", "")},
        ],
        "telecom": [{"system": "phone", "value": hospital.get("phone", "")}],
        "address": [{"text": hospital.get("address", ""), "city": hospital.get("city", "")}],
    }


def create_coverage_resource(policy: dict, patient_id: str) -> dict:
    """Create a FHIR Coverage resource from policy data."""
    return {
        "resourceType": "Coverage",
        "id": str(policy.get("id", "")),
        "status": "active" if policy.get("is_active") else "cancelled",
        "type": {"coding": [{"code": policy.get("policy_type", "")}]},
        "subscriber": {"reference": f"Patient/{patient_id}"},
        "beneficiary": {"reference": f"Patient/{patient_id}"},
        "period": {
            "start": str(policy.get("valid_from", "")),
            "end": str(policy.get("valid_until", "")),
        },
        "payor": [{"display": policy.get("insurer_name", "")}],
    }


def _fhir_gender(gender: str) -> str:
    mapping = {"M": "male", "F": "female", "O": "other", "male": "male", "female": "female"}
    return mapping.get(gender, "unknown")
