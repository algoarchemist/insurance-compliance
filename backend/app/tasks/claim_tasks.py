"""Claim-related Celery tasks — async NHCX polling."""

import asyncio
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=48, default_retry_delay=900)
def poll_claim_status(self, claim_id: str, nhcx_claim_id: str):
    """Poll NHCX claim status every 15 minutes for up to 12 hours."""
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(_poll_claim(claim_id, nhcx_claim_id))
        if result.get("status") in ("settled", "rejected", "partial_settled"):
            return result
        raise self.retry()
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {"status": "polling_timeout", "claim_id": claim_id}
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=24, default_retry_delay=300)
def poll_pre_auth_status(self, claim_id: str, pre_auth_id: str):
    """Poll NHCX pre-auth status every 5 minutes for up to 2 hours."""
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(_poll_pre_auth(claim_id, pre_auth_id))
        if result.get("status") in ("pre_auth_approved", "pre_auth_rejected"):
            return result
        raise self.retry()
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {"status": "polling_timeout", "claim_id": claim_id}
    finally:
        loop.close()


@celery_app.task
def trigger_ocr_parsing(claim_id: str, doc_id: str, minio_key: str):
    """Async OCR + AI parsing of uploaded bill."""
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(_run_ocr(claim_id, doc_id, minio_key))
        return result
    finally:
        loop.close()


@celery_app.task
def verify_bank_account(bank_account_id: str):
    """Penny drop verification via Razorpay."""
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(_verify_bank(bank_account_id))
        return result
    finally:
        loop.close()


async def _poll_claim(claim_id: str, nhcx_claim_id: str):
    from app.services.nhcx_service import poll_claim_status as nhcx_poll
    from app.core.database import async_session
    from app.models.claim import Claim, ClaimStatusHistory
    from sqlalchemy import select
    from uuid import UUID

    result = await nhcx_poll(nhcx_claim_id)
    new_status = result.get("status", "processing")

    async with async_session() as session:
        stmt = select(Claim).where(Claim.id == UUID(claim_id))
        db_result = await session.execute(stmt)
        claim = db_result.scalar_one_or_none()
        if claim and claim.status != new_status:
            claim.status = new_status
            if result.get("approved_amount"):
                claim.approved_amount = result["approved_amount"]
            if result.get("settled_amount"):
                claim.settled_amount = result["settled_amount"]
            history = ClaimStatusHistory(
                claim_id=claim.id,
                status=new_status,
                notes=result.get("notes"),
                changed_by="nhcx",
            )
            session.add(history)
            await session.commit()

    return result


async def _poll_pre_auth(claim_id: str, pre_auth_id: str):
    from app.services.nhcx_service import poll_pre_auth_status as nhcx_poll
    from app.core.database import async_session
    from app.models.claim import Claim, ClaimStatusHistory
    from sqlalchemy import select
    from uuid import UUID

    result = await nhcx_poll(pre_auth_id)
    new_status = result.get("status", "pre_auth_pending")

    async with async_session() as session:
        stmt = select(Claim).where(Claim.id == UUID(claim_id))
        db_result = await session.execute(stmt)
        claim = db_result.scalar_one_or_none()
        if claim and claim.status != new_status:
            claim.status = new_status
            if result.get("approved_amount"):
                claim.approved_amount = result["approved_amount"]
            history = ClaimStatusHistory(
                claim_id=claim.id,
                status=new_status,
                notes=result.get("notes"),
                changed_by="nhcx",
            )
            session.add(history)
            await session.commit()

    return result


async def _run_ocr(claim_id: str, doc_id: str, minio_key: str):
    from app.services.ocr_service import extract_bill_with_ocr
    from app.core.database import async_session
    from app.models.claim import Claim
    from sqlalchemy import select
    from uuid import UUID

    result = await extract_bill_with_ocr(minio_key)

    async with async_session() as session:
        stmt = select(Claim).where(Claim.id == UUID(claim_id))
        db_result = await session.execute(stmt)
        claim = db_result.scalar_one_or_none()
        if claim:
            claim.ocr_extracted = result
            await session.commit()

    return result


async def _verify_bank(bank_account_id: str):
    from app.services.bank_service import verify_bank_account_penny_drop
    from app.core.database import async_session
    from app.core.security import decrypt_bank_account
    from app.models.claim import BankAccount
    from sqlalchemy import select
    from uuid import UUID

    async with async_session() as session:
        stmt = select(BankAccount).where(BankAccount.id == UUID(bank_account_id))
        db_result = await session.execute(stmt)
        account = db_result.scalar_one_or_none()
        if not account:
            return {"verified": False, "error": "Account not found"}

        try:
            plain_account = decrypt_bank_account(account.account_number)
        except Exception:
            plain_account = account.account_number

        result = await verify_bank_account_penny_drop(
            plain_account, account.ifsc_code, account.account_holder or ""
        )

        account.is_verified = result.get("verified", False)
        if result.get("bank_name"):
            account.bank_name = result["bank_name"]
        await session.commit()

    return result
