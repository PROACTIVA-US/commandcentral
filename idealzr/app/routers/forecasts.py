"""
Forecasts router - predictions and forecasting.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from datetime import datetime

from ..database import get_session
from ..services.forecast_service import ForecastService

router = APIRouter()


class ForecastCreate(BaseModel):
    """Schema for creating a forecast."""
    title: str
    description: Optional[str] = None
    prediction: str  # The actual prediction statement
    target_metric: Optional[str] = None
    target_value: Optional[float] = None
    target_unit: Optional[str] = None
    current_value: Optional[float] = None
    confidence: float = 0.5
    resolution_date: datetime  # When will we know the outcome?
    project_id: Optional[str] = None
    hypothesis_id: Optional[str] = None
    goal_id: Optional[str] = None
    owner_id: Optional[str] = None
    methodology: Optional[str] = None  # How was this forecast made?
    assumptions: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    extra_data: dict = Field(default_factory=dict)


class ForecastUpdate(BaseModel):
    """Schema for updating a forecast."""
    title: Optional[str] = None
    description: Optional[str] = None
    prediction: Optional[str] = None
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    confidence: Optional[float] = None
    resolution_date: Optional[datetime] = None
    methodology: Optional[str] = None
    assumptions: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    extra_data: Optional[dict] = None


class ForecastResponse(BaseModel):
    """Schema for forecast response."""
    id: str
    title: str
    description: Optional[str]
    prediction: str
    target_metric: Optional[str]
    target_value: Optional[float]
    target_unit: Optional[str]
    current_value: Optional[float]
    confidence: float
    resolution_date: datetime
    status: str  # pending, correct, incorrect, partial
    project_id: Optional[str]
    hypothesis_id: Optional[str]
    goal_id: Optional[str]
    owner_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class ForecastResolution(BaseModel):
    """Schema for resolving a forecast."""
    status: str  # correct, incorrect, partial
    actual_value: Optional[float] = None
    notes: Optional[str] = None
    resolved_by: Optional[str] = None


@router.get("")
async def list_forecasts(
    project_id: Optional[str] = None,
    hypothesis_id: Optional[str] = None,
    status: Optional[str] = None,
    upcoming_days: Optional[int] = None,
    db: AsyncSession = Depends(get_session),
):
    """List forecasts with optional filtering."""
    service = ForecastService(db)
    return await service.list_forecasts(
        project_id=project_id,
        hypothesis_id=hypothesis_id,
        status=status,
        upcoming_days=upcoming_days,
    )


@router.post("", status_code=201)
async def create_forecast(
    forecast: ForecastCreate,
    db: AsyncSession = Depends(get_session),
):
    """Create a new forecast."""
    service = ForecastService(db)
    return await service.create_forecast(forecast.model_dump())


@router.get("/{forecast_id}")
async def get_forecast(
    forecast_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Get a specific forecast."""
    service = ForecastService(db)
    forecast = await service.get_forecast(forecast_id)
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")
    return forecast


@router.patch("/{forecast_id}")
async def update_forecast(
    forecast_id: str,
    updates: ForecastUpdate,
    db: AsyncSession = Depends(get_session),
):
    """Update a forecast."""
    service = ForecastService(db)
    forecast = await service.update_forecast(
        forecast_id, updates.model_dump(exclude_unset=True)
    )
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")
    return forecast


@router.post("/{forecast_id}/resolve")
async def resolve_forecast(
    forecast_id: str,
    resolution: ForecastResolution,
    db: AsyncSession = Depends(get_session),
):
    """Resolve a forecast with actual outcome."""
    service = ForecastService(db)
    forecast = await service.resolve_forecast(forecast_id, resolution.model_dump())
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")
    return forecast


@router.get("/accuracy/summary")
async def get_accuracy_summary(
    project_id: Optional[str] = None,
    owner_id: Optional[str] = None,
    db: AsyncSession = Depends(get_session),
):
    """Get forecast accuracy summary."""
    service = ForecastService(db)
    return await service.get_accuracy_summary(project_id=project_id, owner_id=owner_id)


@router.delete("/{forecast_id}", status_code=204)
async def delete_forecast(
    forecast_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Delete a forecast."""
    service = ForecastService(db)
    success = await service.delete_forecast(forecast_id)
    if not success:
        raise HTTPException(status_code=404, detail="Forecast not found")
