"""Eligibility service — Multi-scheme eligibility scoring."""

from app.services.ai_service import check_eligibility
from app.services.nha_service import check_pmjay_eligibility


async def check_all_eligibility(user_profile: dict, aadhaar_hash: str = "", language: str = "en") -> dict:
    """
    Check eligibility across all known schemes.
    Combines NHA PMJAY API check with AI-based scoring.
    """
    results = []

    # 1. PMJAY API check
    try:
        pmjay_result = await check_pmjay_eligibility(aadhaar_hash, user_profile)
        results.append({
            "scheme_name": "Ayushman Bharat PMJAY",
            "eligible": pmjay_result.get("eligible", False),
            "score": 0.99 if pmjay_result.get("eligible") else 0.1,
            "reason": "Verified via NHA API" if pmjay_result.get("eligible") else "Not eligible per NHA records",
            "enrollment_steps": ["Visit nearest CSC center", "Bring Aadhaar and ration card"],
        })
    except Exception:
        pass

    # 2. AI-based scoring for all schemes
    ai_results = await check_eligibility(user_profile, language)
    for scheme in ai_results:
        # Don't duplicate PMJAY if already checked
        if scheme.get("scheme_name") == "Ayushman Bharat PMJAY" and results:
            continue
        results.append(scheme)

    return {"schemes": results}
