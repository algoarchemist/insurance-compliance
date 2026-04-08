"""FHIR R4 bundle builder service."""

import uuid
from datetime import datetime, timezone


def build_coverage_eligibility_bundle(patient: dict, policy: dict, hospital: dict) -> dict:
    """Build FHIR R4 CoverageEligibilityRequest bundle."""
    bundle_id = str(uuid.uuid4())
    patient_id = str(patient.get("id", uuid.uuid4()))

    return {
        "resourceType": "Bundle",
        "id": bundle_id,
        "type": "collection",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entry": [
            {
                "fullUrl": f"urn:uuid:{patient_id}",
                "resource": {
                    "resourceType": "Patient",
                    "id": patient_id,
                    "name": [{"text": patient.get("full_name", "")}],
                    "birthDate": str(patient.get("date_of_birth", "")),
                    "gender": _map_gender(patient.get("gender", "")),
                    "identifier": [
                        {
                            "system": "https://ndhm.gov.in/patients",
                            "value": patient.get("abha_number", ""),
                        }
                    ],
                },
            },
            {
                "fullUrl": f"urn:uuid:{uuid.uuid4()}",
                "resource": {
                    "resourceType": "Coverage",
                    "status": "active",
                    "type": {
                        "coding": [{"code": policy.get("policy_type", "private")}]
                    },
                    "subscriber": {"reference": f"Patient/{patient_id}"},
                    "beneficiary": {"reference": f"Patient/{patient_id}"},
                    "payor": [{"display": policy.get("insurer_name", "")}],
                },
            },
            {
                "fullUrl": f"urn:uuid:{uuid.uuid4()}",
                "resource": {
                    "resourceType": "CoverageEligibilityRequest",
                    "status": "active",
                    "purpose": ["benefits"],
                    "patient": {"reference": f"Patient/{patient_id}"},
                    "created": datetime.now(timezone.utc).isoformat(),
                    "provider": {
                        "display": hospital.get("name", ""),
                    },
                },
            },
        ],
    }


def build_pre_auth_bundle(
    patient: dict, policy: dict, hospital: dict,
    procedure: dict, estimated_amount: float
) -> dict:
    """Build FHIR R4 Claim bundle for pre-authorization."""
    bundle_id = str(uuid.uuid4())
    patient_id = str(patient.get("id", uuid.uuid4()))
    claim_id = str(uuid.uuid4())

    return {
        "resourceType": "Bundle",
        "id": bundle_id,
        "type": "collection",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entry": [
            {
                "fullUrl": f"urn:uuid:{patient_id}",
                "resource": {
                    "resourceType": "Patient",
                    "id": patient_id,
                    "name": [{"text": patient.get("full_name", "")}],
                    "birthDate": str(patient.get("date_of_birth", "")),
                    "gender": _map_gender(patient.get("gender", "")),
                },
            },
            {
                "fullUrl": f"urn:uuid:{claim_id}",
                "resource": {
                    "resourceType": "Claim",
                    "id": claim_id,
                    "status": "active",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                                "code": "institutional",
                            }
                        ]
                    },
                    "use": "preauthorization",
                    "patient": {"reference": f"Patient/{patient_id}"},
                    "created": datetime.now(timezone.utc).isoformat(),
                    "provider": {"display": hospital.get("name", "")},
                    "priority": {"coding": [{"code": "normal"}]},
                    "diagnosis": [
                        {
                            "sequence": 1,
                            "diagnosisCodeableConcept": {
                                "coding": [
                                    {
                                        "system": "http://hl7.org/fhir/sid/icd-10",
                                        "code": procedure.get("procedure_code", ""),
                                        "display": procedure.get("procedure_name", ""),
                                    }
                                ]
                            },
                        }
                    ],
                    "total": {"value": estimated_amount, "currency": "INR"},
                },
            },
        ],
    }


def build_claim_bundle(
    patient: dict, policy: dict, hospital: dict,
    ocr_items: list, pre_auth_ref: str, documents: list
) -> dict:
    """Build FHIR R4 Claim bundle from OCR data."""
    bundle_id = str(uuid.uuid4())
    patient_id = str(patient.get("id", uuid.uuid4()))
    claim_id = str(uuid.uuid4())

    items = []
    for i, item in enumerate(ocr_items, 1):
        fhir_item = {
            "sequence": i,
            "productOrService": {
                "text": item.get("description", ""),
            },
            "unitPrice": {
                "value": float(item.get("amount", 0)),
                "currency": "INR",
            },
        }
        if item.get("quantity"):
            fhir_item["quantity"] = {"value": item["quantity"]}
        items.append(fhir_item)

    total = sum(float(item.get("amount", 0)) for item in ocr_items)

    claim_resource = {
        "resourceType": "Claim",
        "id": claim_id,
        "status": "active",
        "type": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                    "code": "institutional",
                }
            ]
        },
        "use": "claim",
        "patient": {"reference": f"Patient/{patient_id}"},
        "created": datetime.now(timezone.utc).isoformat(),
        "provider": {"display": hospital.get("name", "")},
        "priority": {"coding": [{"code": "normal"}]},
        "item": items,
        "total": {"value": total, "currency": "INR"},
    }

    if pre_auth_ref:
        claim_resource["related"] = [
            {"claim": {"identifier": {"value": pre_auth_ref}}, "relationship": {"coding": [{"code": "prior"}]}}
        ]

    return {
        "resourceType": "Bundle",
        "id": bundle_id,
        "type": "collection",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entry": [
            {
                "fullUrl": f"urn:uuid:{patient_id}",
                "resource": {
                    "resourceType": "Patient",
                    "id": patient_id,
                    "name": [{"text": patient.get("full_name", "")}],
                },
            },
            {"fullUrl": f"urn:uuid:{claim_id}", "resource": claim_resource},
        ],
    }


def validate_fhir_bundle(bundle: dict) -> list:
    """Validate FHIR bundle structure. Returns list of errors."""
    errors = []
    if not bundle.get("resourceType") == "Bundle":
        errors.append("Missing or invalid resourceType")
    if not bundle.get("entry"):
        errors.append("Bundle has no entries")
    for i, entry in enumerate(bundle.get("entry", [])):
        resource = entry.get("resource", {})
        if not resource.get("resourceType"):
            errors.append(f"Entry {i}: missing resourceType")
    return errors


def _map_gender(gender: str) -> str:
    """Map gender codes to FHIR values."""
    mapping = {"M": "male", "F": "female", "O": "other", "male": "male", "female": "female"}
    return mapping.get(gender, "unknown")
