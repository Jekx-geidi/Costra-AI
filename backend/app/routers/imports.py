import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.billing_source import BillingSource
from app.models.user import User
from app.auth.dependencies import require_billing_admin, require_viewer
from app.schemas.imports import ImportResponse, ImportHistoryItem
from app.services.ingestion.file_processor import FileProcessor
from app.utils.audit import write_audit

router = APIRouter()


@router.post("", response_model=ImportResponse, status_code=status.HTTP_201_CREATED)
async def upload_invoice(
    account_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_billing_admin),
):
    processor = FileProcessor(db)
    result = await processor.process(file=file, account_id=account_id, actor=actor)
    await write_audit(
        db, action="upload", resource_type="billing_source",
        resource_id=result.id, actor=actor,
        metadata={"filename": file.filename, "source_type": result.source_type},
    )
    return result


@router.get("/{import_id}", response_model=ImportResponse)
async def get_import(
    import_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_viewer),
):
    result = await db.execute(select(BillingSource).where(BillingSource.id == import_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import not found")
    return source


@router.get("", response_model=list[ImportHistoryItem])
async def list_imports(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_viewer),
):
    result = await db.execute(select(BillingSource).order_by(BillingSource.imported_at.desc()).limit(100))
    return result.scalars().all()
