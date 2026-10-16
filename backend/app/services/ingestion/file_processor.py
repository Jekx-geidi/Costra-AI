import csv
import io
import os
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.config import settings
from app.models.billing_source import BillingSource
from app.models.billing_account import BillingAccount
from app.models.user import User
from app.schemas.imports import ImportResponse, ParsedLineItem
from app.services.deduplication import compute_file_hash, upsert_billing_record
from app.services.normalization import (
    normalize_expense_category,
    normalize_financial_basis,
    normalize_currency,
    normalize_amount,
)


class FileProcessor:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def process(self, file: UploadFile, account_id: uuid.UUID, actor: User) -> ImportResponse:
        ext = (file.filename or "").rsplit(".", 1)[-1].lower()
        if ext not in settings.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File type '.{ext}' not allowed. Accepted: {settings.allowed_extensions}",
            )

        content = await file.read()
        if len(content) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"File exceeds {settings.max_upload_size_mb} MB limit",
            )

        file_hash = compute_file_hash(content)

        existing = await self.db.execute(
            select(BillingSource).where(BillingSource.source_hash == file_hash)
        )
        dup = existing.scalar_one_or_none()
        if dup:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"File already imported (source id: {dup.id})",
            )

        account_result = await self.db.execute(
            select(BillingAccount).where(BillingAccount.id == account_id)
        )
        account = account_result.scalar_one_or_none()
        if not account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing account not found")

        if ext == "csv":
            parsed, warnings = self._parse_csv(content, account.default_currency)
        else:
            parsed, warnings = self._parse_pdf(content, account.default_currency)

        requires_review = bool(warnings) or any(p.confidence != "high" for p in parsed)

        storage_path = Path(settings.invoice_storage_path)
        storage_path.mkdir(parents=True, exist_ok=True)
        stored_filename = f"{uuid.uuid4()}.{ext}"
        (storage_path / stored_filename).write_bytes(content)

        source = BillingSource(
            account_id=account_id,
            source_type=ext,
            source_reference=stored_filename,
            source_hash=file_hash,
            status="imported" if requires_review else "validated",
        )
        self.db.add(source)
        await self.db.flush()

        if not requires_review:
            for item in parsed:
                fallback_id = f"file:{file_hash}:{item.description or ''}:{item.amount}"
                await upsert_billing_record(
                    self.db,
                    account_id=account_id,
                    source_id=source.id,
                    provider=account.provider,
                    external_record_id=fallback_id,
                    expense_category=item.expense_category,
                    financial_basis=item.financial_basis,
                    description=item.description,
                    period_start=self._parse_date(item.period_start),
                    period_end=self._parse_date(item.period_end),
                    quantity=None,
                    amount=item.amount,
                    currency=item.currency,
                    validation_status="pending",
                )

        return ImportResponse(
            id=source.id,
            account_id=account_id,
            source_type=ext,
            status=source.status,
            source_hash=file_hash,
            billing_period_start=None,
            billing_period_end=None,
            parsed_items=parsed,
            validation_warnings=warnings,
            requires_review=requires_review,
            imported_at=source.imported_at,
        )

    def _parse_csv(self, content: bytes, default_currency: str) -> tuple[list[ParsedLineItem], list[str]]:
        items: list[ParsedLineItem] = []
        warnings: list[str] = []
        text = content.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        for i, row in enumerate(reader, start=2):
            try:
                amount = normalize_amount(row.get("amount") or row.get("total") or row.get("cost") or "0")
                currency = normalize_currency(row.get("currency"), default_currency)
                category = normalize_expense_category(row.get("category") or row.get("type"))
                basis = normalize_financial_basis(row.get("basis") or row.get("financial_basis"))
                desc = row.get("description") or row.get("name") or row.get("item")
                items.append(ParsedLineItem(
                    description=desc,
                    expense_category=category,
                    financial_basis=basis,
                    period_start=row.get("period_start") or row.get("start_date"),
                    period_end=row.get("period_end") or row.get("end_date"),
                    amount=amount,
                    currency=currency,
                    confidence="high",
                ))
            except (ValueError, KeyError) as exc:
                warnings.append(f"Row {i}: {exc}")
        return items, warnings

    def _parse_pdf(self, content: bytes, default_currency: str) -> tuple[list[ParsedLineItem], list[str]]:
        warnings: list[str] = []
        items: list[ParsedLineItem] = []
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

            import re
            amount_matches = re.findall(r"\$\s*([\d,]+\.\d{2})", full_text)
            if not amount_matches:
                warnings.append("No recognizable monetary amounts found in PDF — manual review required")
                return items, warnings

            for raw_amount in amount_matches[:20]:
                try:
                    amount = Decimal(raw_amount.replace(",", ""))
                    items.append(ParsedLineItem(
                        description="Extracted from PDF",
                        expense_category="api",
                        financial_basis="invoiced",
                        period_start=None,
                        period_end=None,
                        amount=amount,
                        currency=default_currency,
                        confidence="low",
                    ))
                except InvalidOperation:
                    pass

            if items:
                warnings.append("PDF amounts extracted with low confidence — please verify each line before confirming")
        except Exception as exc:
            warnings.append(f"PDF parsing failed: {exc} — manual entry required")

        return items, warnings

    @staticmethod
    def _parse_date(raw: str | None) -> date | None:
        if not raw:
            return None
        from datetime import datetime
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(raw.strip(), fmt).date()
            except ValueError:
                continue
        return None
