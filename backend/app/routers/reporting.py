from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.auth.dependencies import require_viewer
from app.schemas.reporting import SummaryResponse, TrendResponse
from app.services.reporting import ReportingService

router = APIRouter()


@router.get("/summary", response_model=SummaryResponse)
async def summary(
    period: str = Query(..., description="YYYY-MM"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_viewer),
):
    svc = ReportingService(db)
    return await svc.get_summary(period)


@router.get("/trends", response_model=TrendResponse)
async def trends(
    months: int = Query(12, ge=1, le=36),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_viewer),
):
    svc = ReportingService(db)
    return await svc.get_trends(months)
