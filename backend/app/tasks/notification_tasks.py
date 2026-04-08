"""Notification-related Celery tasks."""

from app.tasks.celery_app import celery_app
import asyncio


@celery_app.task
def send_claim_status_sms(phone: str, claim_id: str, status: str):
    """Send SMS notification when claim status changes."""
    status_messages = {
        "pre_auth_approved": "Your pre-authorization has been approved! Claim ID: {claim_id}",
        "pre_auth_rejected": "Your pre-authorization was rejected. Claim ID: {claim_id}. Please check the app for details.",
        "submitted": "Your claim {claim_id} has been submitted successfully.",
        "processing": "Your claim {claim_id} is being processed.",
        "settled": "Great news! Your claim {claim_id} has been settled.",
        "rejected": "Your claim {claim_id} has been rejected. Check the app for AI explanation and next steps.",
        "partial_settled": "Your claim {claim_id} has been partially settled. Check app for details.",
        "query_raised": "A query has been raised on your claim {claim_id}. Please respond in the app.",
    }

    message = status_messages.get(status, f"Your claim {claim_id} status updated to: {status}")
    message = message.format(claim_id=claim_id[:8])

    loop = asyncio.new_event_loop()
    try:
        from app.services.sms_service import send_notification_sms
        loop.run_until_complete(send_notification_sms(phone, f"[Sugamai] {message}"))
    finally:
        loop.close()


@celery_app.task
def send_caregiver_notification(caregiver_phone: str, elder_name: str, action: str):
    """Notify caregiver about elder's actions."""
    message = f"[Sugamai] {elder_name}'s health insurance: {action}"
    loop = asyncio.new_event_loop()
    try:
        from app.services.sms_service import send_notification_sms
        loop.run_until_complete(send_notification_sms(caregiver_phone, message))
    finally:
        loop.close()
