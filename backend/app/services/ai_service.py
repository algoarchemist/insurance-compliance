"""AI service — Claude API calls for eligibility, gap detection, explanations."""

import json
from typing import Optional

from config import settings

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


def _get_client():
    if HAS_ANTHROPIC and settings.ANTHROPIC_API_KEY:
        return anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return None


async def check_eligibility(user_profile: dict, language: str = "en") -> list:
    """Score user against all known government health schemes."""
    client = _get_client()
    if not client:
        return _mock_eligibility(user_profile)

    prompt = (
        "You are a health insurance eligibility expert for India. "
        "Given the following user profile, score them against all known government health insurance schemes. "
        "Return ONLY valid JSON array of objects with: scheme_name, eligible (bool), score (0-1), "
        "reason (string explaining why), enrollment_steps (array of strings).\n\n"
        "Known schemes: Ayushman Bharat PMJAY, Tamil Nadu CMCHIS, Delhi Mukhyamantri Swasthya Bima, "
        "Andhra Pradesh Aarogyasri, Kerala Karunya, West Bengal Swasthya Sathi, "
        "ESI (for organized sector), CGHS (for central govt employees).\n\n"
        f"User Profile: {json.dumps(user_profile)}\n"
        f"Respond in: {language}"
    )

    message = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        return json.loads(message.content[0].text)
    except (json.JSONDecodeError, IndexError):
        return _mock_eligibility(user_profile)


async def generate_coverage_summary(coverage_grid: dict, language: str) -> str:
    """Convert coverage dict into plain language summary."""
    client = _get_client()
    if not client:
        return "Surgery and ICU are fully covered. General ward has daily limits. Private ward and OPD are not covered."

    prompt = (
        "Convert this hospital coverage grid into a 3-line plain language summary "
        f"in {language} language. Be concise and helpful for a patient.\n\n"
        f"Coverage: {json.dumps(coverage_grid)}"
    )

    message = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


async def explain_rejection(rejection_code: str, claim_data: dict, language: str) -> dict:
    """Explain NHCX rejection code in plain language."""
    rejection_map = {
        "NHCX_REJ_001": "Duplicate claim — a similar claim already exists",
        "NHCX_REJ_002": "Policy not active at time of treatment",
        "NHCX_REJ_003": "Hospital not empanelled under this policy",
        "NHCX_REJ_004": "Missing required documents",
        "NHCX_REJ_005": "Claim amount exceeds policy limit",
    }

    client = _get_client()
    if not client:
        base = rejection_map.get(rejection_code, "Unknown rejection reason")
        return {
            "explanation": base,
            "remediation_steps": ["Contact your TPA for details", "Resubmit with corrections"],
        }

    prompt = (
        f"Explain this health insurance claim rejection to a patient in {language}. "
        f"Rejection code: {rejection_code} — {rejection_map.get(rejection_code, 'Unknown')}. "
        f"Claim details: {json.dumps(claim_data)}. "
        "Return JSON with: explanation (string), remediation_steps (array of strings). "
        "Be empathetic, clear, and actionable."
    )

    message = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        return json.loads(message.content[0].text)
    except (json.JSONDecodeError, IndexError):
        return {
            "explanation": rejection_map.get(rejection_code, "Claim was rejected"),
            "remediation_steps": ["Contact your TPA", "Review and resubmit"],
        }


async def detect_claim_gaps(claim: dict, uploaded_docs: list, fhir_bundle: dict) -> list:
    """Check claim completeness before NHCX submission."""
    gaps = []
    doc_types = [d.get("doc_type") for d in uploaded_docs] if uploaded_docs else []

    if "hospital_bill" not in doc_types:
        gaps.append({"field": "hospital_bill", "severity": "required", "message": "Hospital bill document is missing"})
    if "discharge_summary" not in doc_types:
        gaps.append({"field": "discharge_summary", "severity": "required", "message": "Discharge summary document is missing"})
    if not claim.get("ocr_extracted"):
        gaps.append({"field": "ocr_data", "severity": "required", "message": "Bill has not been parsed (OCR required)"})

    # Additional AI gap detection
    client = _get_client()
    if client and fhir_bundle:
        try:
            prompt = (
                "Review this FHIR claim bundle and list any missing required fields for NHCX submission. "
                "Return ONLY JSON array of {field, severity, message}. If everything looks good, return empty array.\n\n"
                f"Bundle: {json.dumps(fhir_bundle)}"
            )
            message = await client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            ai_gaps = json.loads(message.content[0].text)
            gaps.extend(ai_gaps)
        except Exception:
            pass

    return gaps


async def generate_admission_checklist(hospital: dict, policy: dict, procedure: str) -> list:
    """Generate list of documents to carry for hospital admission."""
    client = _get_client()
    base_checklist = [
        "Aadhaar card (original + photocopy)",
        "Health insurance policy document",
        "ABHA health card (if available)",
        "Doctor referral letter",
        "Photo ID proof",
        "Recent passport-size photographs (2 nos)",
        "Previous medical reports (if any)",
    ]

    if not client:
        return base_checklist

    try:
        prompt = (
            f"Generate a hospital admission checklist for a patient going to {hospital.get('name', 'hospital')} "
            f"for {procedure} under {policy.get('insurer_name', 'insurance')} policy "
            f"(type: {policy.get('policy_type', 'private')}). "
            "Return ONLY a JSON array of strings. Include all necessary documents and items."
        )
        message = await client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(message.content[0].text)
    except Exception:
        return base_checklist


async def chat_eligibility(messages: list, language: str = "en") -> str:
    """Conversational eligibility assistant."""
    client = _get_client()
    if not client:
        return "I'm Sugamai, your health insurance assistant. I can help you understand which government schemes you qualify for. Please provide your annual income, family size, and state of residence."

    system_prompt = (
        "You are Sugamai, a helpful health insurance assistant for Indian citizens. "
        "Help users understand which government health insurance schemes they qualify for. "
        "Ask about income, family size, state, BPL card status, age, and employment type. "
        f"Respond in {language}. Be warm, empathetic, and clear. "
        "Known schemes: PMJAY, CMCHIS (TN), Mukhyamantri Swasthya Bima (Delhi), Aarogyasri (AP), "
        "Karunya (Kerala), Swasthya Sathi (WB), ESI, CGHS."
    )

    formatted_messages = []
    for msg in messages:
        formatted_messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", ""),
        })

    message = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=1000,
        system=system_prompt,
        messages=formatted_messages,
    )
    return message.content[0].text


def _mock_eligibility(profile: dict) -> list:
    """Mock eligibility results for development."""
    schemes = [
        {
            "scheme_name": "Ayushman Bharat PMJAY",
            "eligible": profile.get("income_annual", 0) < 500000,
            "score": 0.95 if profile.get("income_annual", 0) < 500000 else 0.1,
            "reason": "You qualify — income below ₹5 lakh" if profile.get("income_annual", 0) < 500000 else "Income exceeds ₹5 lakh limit",
            "enrollment_steps": ["Visit nearest CSC center", "Bring Aadhaar and ration card"],
        },
        {
            "scheme_name": "Tamil Nadu CMCHIS",
            "eligible": profile.get("state") == "TN" and profile.get("income_annual", 0) < 300000,
            "score": 0.85 if profile.get("state") == "TN" else 0.0,
            "reason": "Tamil Nadu state scheme for residents" if profile.get("state") == "TN" else "Not applicable — TN residents only",
            "enrollment_steps": ["Apply at district collector office", "Bring family ration card"],
        },
    ]
    return schemes
