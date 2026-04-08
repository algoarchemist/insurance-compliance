"""AI Pydantic schemas."""

from typing import Optional, List

from pydantic import BaseModel


class EligibilityChatRequest(BaseModel):
    message: str
    history: List[dict] = []


class EligibilityChatResponse(BaseModel):
    reply: str
    schemes_identified: List[dict] = []


class CoverageSummarizeRequest(BaseModel):
    coverage_grid: dict
    language: str = "en"


class CoverageSummarizeResponse(BaseModel):
    summary: str


class RejectionExplainRequest(BaseModel):
    rejection_code: str
    claim_id: str
    language: str = "en"


class RejectionExplainResponse(BaseModel):
    explanation: str
    remediation_steps: List[str] = []


class BillParseRequest(BaseModel):
    doc_id: str


class BillParseResponse(BaseModel):
    extracted_items: List[dict]
    totals: dict
    metadata: dict


class ChecklistRequest(BaseModel):
    hospital_id: str
    policy_id: str
    procedure: str


class ChecklistResponse(BaseModel):
    checklist: List[str]
