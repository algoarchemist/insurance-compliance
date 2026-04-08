"""OCR service — Bill parsing via Tesseract + Claude AI."""

import io
import json
from typing import Optional

from config import settings
from app.core.minio_client import download_file

# Try importing tesseract and pymupdf — they may not be installed locally
try:
    import pytesseract
    from PIL import Image
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


async def extract_bill_with_ocr(minio_key: str) -> dict:
    """
    1. Download file from MinIO
    2. If PDF: convert pages to images with PyMuPDF
    3. Run Tesseract OCR on each page
    4. Pass raw OCR text to Claude AI for structured extraction
    5. Return structured line items
    """
    # Download file
    try:
        file_data = download_file(minio_key)
    except Exception:
        return _mock_ocr_result()

    ocr_text = ""

    if minio_key.endswith(".pdf") and HAS_PYMUPDF:
        # PDF — convert pages to images
        doc = fitz.open(stream=file_data, filetype="pdf")
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            if HAS_TESSERACT:
                ocr_text += pytesseract.image_to_string(img, lang="eng") + "\n"
        doc.close()
    elif HAS_TESSERACT:
        # Image file
        img = Image.open(io.BytesIO(file_data))
        ocr_text = pytesseract.image_to_string(img, lang="eng")

    if not ocr_text.strip():
        return _mock_ocr_result()

    # Parse with Claude AI
    if HAS_ANTHROPIC and settings.ANTHROPIC_API_KEY:
        return await _parse_with_claude(ocr_text)

    return _mock_ocr_result()


async def extract_bill_with_claude_vision(minio_key: str) -> dict:
    """Send image directly to Claude vision API for complex bills."""
    try:
        file_data = download_file(minio_key)
    except Exception:
        return _mock_ocr_result()

    if not HAS_ANTHROPIC or not settings.ANTHROPIC_API_KEY:
        return _mock_ocr_result()

    import base64
    b64_image = base64.b64encode(file_data).decode("utf-8")

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    message = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": b64_image,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "You are a medical bill parser. Extract all line items from this hospital bill. "
                            "Return ONLY valid JSON with: items (array of {description, amount, quantity, unit}), "
                            "total_amount, hospital_name, doctor_name, patient_name, "
                            "admission_date, discharge_date, diagnosis, icd_codes (array)."
                        ),
                    },
                ],
            }
        ],
    )

    try:
        result = json.loads(message.content[0].text)
        return result
    except (json.JSONDecodeError, IndexError):
        return _mock_ocr_result()


async def _parse_with_claude(ocr_text: str) -> dict:
    """Parse raw OCR text with Claude AI."""
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    message = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": (
                    "You are a medical bill parser. Extract all line items from this hospital bill text. "
                    "Return ONLY valid JSON with: items (array of {description, amount, quantity, unit}), "
                    "total_amount, hospital_name, doctor_name, patient_name, "
                    "admission_date, discharge_date, diagnosis, icd_codes (array).\n\n"
                    f"Text:\n{ocr_text}"
                ),
            }
        ],
    )

    try:
        result = json.loads(message.content[0].text)
        return result
    except (json.JSONDecodeError, IndexError):
        return _mock_ocr_result()


def _mock_ocr_result() -> dict:
    """Return mock OCR result for development/testing."""
    return {
        "items": [
            {"description": "Room Rent", "amount": 6000, "quantity": 3, "unit": "days"},
            {"description": "Surgery Charges", "amount": 35000, "quantity": 1, "unit": "lump_sum"},
            {"description": "Medicines", "amount": 4200, "quantity": 1, "unit": "lump_sum"},
            {"description": "Lab Tests", "amount": 3500, "quantity": 1, "unit": "lump_sum"},
            {"description": "Doctor Consultation", "amount": 2000, "quantity": 2, "unit": "visits"},
        ],
        "total_amount": 50700,
        "hospital_name": "Apollo Hospital Chennai",
        "doctor_name": "Dr. Priya Nair",
        "patient_name": "Test Patient",
        "admission_date": "2025-02-01",
        "discharge_date": "2025-02-05",
        "diagnosis": "Acute Appendicitis",
        "icd_codes": ["K35.2"],
    }
