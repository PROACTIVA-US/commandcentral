"""
Forecast service - business logic for predictions and forecasting.

Note: Forecasts are stored in the database but use a simple table structure
rather than a full SQLAlchemy model. This keeps the service self-contained.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import select, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
import uuid

from ..database import Base
from sqlalchemy import Column, String, Text, DateTime, JSON, Float

logger = structlog.get_logger("idealzr.services.forecast")


# Simple forecast table definition (could be moved to models if needed)
class Forecast(Base):
    """Forecast/prediction with resolution tracking."""
    
    __tablename__ = "forecasts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    prediction = Column(Text, nullable=False)
    target_metric = Column(String, nullable=True)
    target_value = Column(Float, nullable=True)
    target_unit = Column(String, nullable=True)
    current_value = Column(Float, nullable=True)
    actual_value = Column(Float, nullable=True)
    confidence = Column(Float, default=0.5)
    resolution_date = Column(DateTime, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending")  # pending, correct, incorrect, partial
    resolution_notes = Column(Text, nullable=True)
    project_id = Column(String, nullable=True, index=True)
    hypothesis_id = Column(String, nullable=True, index=True)
    goal_id = Column(String, nullable=True, index=True)
    owner_id = Column(String, nullable=True)
    methodology = Column(Text, nullable=True)
    assumptions = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    extra_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ForecastService:
    """Service for managing forecasts and predictions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_forecast(self, data: dict) -> Forecast:
        """Create a new forecast."""
        forecast = Forecast(**data)
        self.db.add(forecast)
        await self.db.flush()
        
        await logger.ainfo(
            "forecast_created",
            forecast_id=forecast.id,
            title=forecast.title,
            resolution_date=forecast.resolution_date.isoformat(),
        )
        
        return forecast

    async def get_forecast(self, forecast_id: str) -> Optional[Forecast]:
        """Get a forecast by ID."""
        result = await self.db.execute(
            select(Forecast).where(Forecast.id == forecast_id)
        )
        return result.scalar_one_or_none()

    async def list_forecasts(
        self,
        project_id: Optional[str] = None,
        hypothesis_id: Optional[str] = None,
        status: Optional[str] = None,
        upcoming_days: Optional[int] = None,
    ) -> List[Forecast]:
        """List forecasts with optional filtering."""
        query = select(Forecast)
        
        filters = []
        if project_id:
            filters.append(Forecast.project_id == project_id)
        if hypothesis_id:
            filters.append(Forecast.hypothesis_id == hypothesis_id)
        if status:
            filters.append(Forecast.status == status)
        if upcoming_days:
            future_date = datetime.utcnow() + timedelta(days=upcoming_days)
            filters.append(Forecast.resolution_date <= future_date)
            filters.append(Forecast.status == "pending")
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(Forecast.resolution_date)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_forecast(self, forecast_id: str, updates: dict) -> Optional[Forecast]:
        """Update a forecast."""
        forecast = await self.get_forecast(forecast_id)
        if not forecast:
            return None

        for field, value in updates.items():
            if hasattr(forecast, field):
                setattr(forecast, field, value)

        await self.db.flush()
        
        await logger.ainfo(
            "forecast_updated",
            forecast_id=forecast_id,
            updates=list(updates.keys()),
        )
        
        return forecast

    async def resolve_forecast(self, forecast_id: str, resolution: dict) -> Optional[Forecast]:
        """Resolve a forecast with actual outcome."""
        forecast = await self.get_forecast(forecast_id)
        if not forecast:
            return None

        forecast.status = resolution.get("status", "correct")
        forecast.actual_value = resolution.get("actual_value")
        forecast.resolution_notes = resolution.get("notes")
        forecast.resolved_at = datetime.utcnow()
        
        if resolution.get("resolved_by"):
            forecast.extra_data["resolved_by"] = resolution["resolved_by"]

        await self.db.flush()
        
        await logger.ainfo(
            "forecast_resolved",
            forecast_id=forecast_id,
            status=forecast.status,
            actual_value=forecast.actual_value,
        )
        
        return forecast

    async def get_accuracy_summary(
        self,
        project_id: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> dict:
        """Get forecast accuracy summary."""
        query = select(Forecast).where(Forecast.status != "pending")
        
        if project_id:
            query = query.where(Forecast.project_id == project_id)
        if owner_id:
            query = query.where(Forecast.owner_id == owner_id)
        
        result = await self.db.execute(query)
        forecasts = result.scalars().all()
        
        if not forecasts:
            return {
                "total_resolved": 0,
                "correct": 0,
                "incorrect": 0,
                "partial": 0,
                "accuracy_rate": 0.0,
                "by_confidence_band": {},
            }
        
        # Count by status
        correct = sum(1 for f in forecasts if f.status == "correct")
        incorrect = sum(1 for f in forecasts if f.status == "incorrect")
        partial = sum(1 for f in forecasts if f.status == "partial")
        
        # Calculate by confidence band
        confidence_bands = {
            "low": {"range": (0, 0.4), "correct": 0, "total": 0},
            "medium": {"range": (0.4, 0.7), "correct": 0, "total": 0},
            "high": {"range": (0.7, 1.0), "correct": 0, "total": 0},
        }
        
        for f in forecasts:
            for band_name, band_data in confidence_bands.items():
                if band_data["range"][0] <= f.confidence < band_data["range"][1]:
                    band_data["total"] += 1
                    if f.status == "correct":
                        band_data["correct"] += 1
                    break
        
        # Calculate accuracy rates for bands
        band_accuracy = {}
        for band_name, band_data in confidence_bands.items():
            if band_data["total"] > 0:
                band_accuracy[band_name] = {
                    "total": band_data["total"],
                    "correct": band_data["correct"],
                    "accuracy": band_data["correct"] / band_data["total"],
                }
        
        return {
            "total_resolved": len(forecasts),
            "correct": correct,
            "incorrect": incorrect,
            "partial": partial,
            "accuracy_rate": correct / len(forecasts) if forecasts else 0.0,
            "by_confidence_band": band_accuracy,
        }

    async def delete_forecast(self, forecast_id: str) -> bool:
        """Delete a forecast."""
        forecast = await self.get_forecast(forecast_id)
        if not forecast:
            return False
        
        await self.db.delete(forecast)
        await self.db.flush()
        
        await logger.ainfo("forecast_deleted", forecast_id=forecast_id)
        return True

    async def get_upcoming_forecasts(self, days: int = 7) -> List[Forecast]:
        """Get forecasts due for resolution soon."""
        future_date = datetime.utcnow() + timedelta(days=days)
        result = await self.db.execute(
            select(Forecast)
            .where(
                Forecast.status == "pending",
                Forecast.resolution_date <= future_date,
            )
            .order_by(Forecast.resolution_date)
        )
        return result.scalars().all()
