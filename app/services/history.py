from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.models import PredictionHistory

async def save_prediction(session: AsyncSession, prediction_result: dict, model_version: str) -> PredictionHistory:
    """
    Simpan Hasil Prediksi ke Database
    """
    record = PredictionHistory(
        input_years = prediction_result["input_years"],
        converted_years = prediction_result["converted_years_decimal"],
        predicted_salaries = prediction_result["estimated_salary_million"],
        data_count = len(prediction_result["input_years"]),
        model_version = model_version,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)

    return record

async def get_all_history(session: AsyncSession, limit: int = 20) -> list[PredictionHistory]:
    result = await session.execute(
        select(PredictionHistory)
        .order_by(desc(PredictionHistory.created_at)).limit(limit)
    )
    return result.scalars().all()

async def get_history_by_id(session: AsyncSession, history_id: int, ) -> PredictionHistory | None :
    result = await session.execute(
        select(PredictionHistory).where(PredictionHistory.id == history_id)
    )
    return result.scalar_one_or_none()