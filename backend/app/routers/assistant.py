import json
import uuid
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_billing_admin, require_viewer
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.assistant import (
    ChatRequest,
    ChatResponse,
    InvoiceConfirmRequest,
    InvoiceConfirmResponse,
    InvoiceDraftResponse,
)
from app.services.assistant.context import build_snapshot
from app.services.assistant.guard import build_system_prompt, sanitize_reply
from app.services.assistant.invoice import confirm_invoice, extract_invoice
from app.services.assistant.llm import chat_completion, ensure_enabled
from app.utils.audit import write_audit

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_viewer),
):
    ensure_enabled()
    snapshot = await build_snapshot(db, user)
    system_prompt = build_system_prompt(
        json.dumps(snapshot, default=str, separators=(",", ":")),
        snapshot["generated_at"],
    )
    # Only user/assistant turns come from the client; the system prompt is always ours.
    history = [m.model_dump() for m in body.messages[-settings.assistant_max_history:]]
    reply = await chat_completion(
        [{"role": "system", "content": system_prompt}, *history],
        max_tokens=settings.assistant_max_tokens,
    )
    return ChatResponse(reply=sanitize_reply(reply))


@router.post("/invoice", response_model=InvoiceDraftResponse)
async def read_invoice(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_billing_admin),
):
    draft = await extract_invoice(db, file)
    await write_audit(
        db, action="assistant_read_invoice", resource_type="invoice_draft", actor=actor,
        metadata={"filename": file.filename, "provider": draft["provider"], "items": len(draft["items"])},
    )
    return draft


@router.post("/invoice/{draft_id}/confirm", response_model=InvoiceConfirmResponse)
async def import_invoice(
    draft_id: uuid.UUID,
    body: InvoiceConfirmRequest,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_billing_admin),
):
    result = await confirm_invoice(
        db,
        draft_id=draft_id,
        account_id=body.account_id,
        invoice_number=body.invoice_number,
        items=[i.model_dump() for i in body.items],
    )
    await write_audit(
        db, action="upload", resource_type="billing_source", resource_id=result["source_id"], actor=actor,
        metadata={"via": "assistant", "records": result["records_imported"],
                  "total": f"{result['total']:.6f}", "currency": result["currency"]},
    )
    return result
