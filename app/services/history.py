import math

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, cast, String
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from app.db.models import PredictionHistory

async def save_prediction(session: AsyncSession, prediction_result: dict, model_version: str) -> PredictionHistory:
    """
    Simpan Hasil Prediksi ke Database.
    Menggunakan .get() untuk field opsional agar kompatibel
    dengan berbagai versi output predictor.
    """
    record = PredictionHistory(
        input_years=prediction_result["input_years"],
        converted_years=prediction_result["converted_years_decimal"],
        city=prediction_result.get("city"),
        job_level=prediction_result.get("job_level"),
        predicted_salaries=prediction_result["estimated_salary_million"],
        data_count=len(prediction_result["input_years"]),
        model_version=model_version,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)

    return record

async def get_all_history(
    session: AsyncSession,
    page: int = 1,
    size: int = 10,
    filter_city: str | None = None,
    filter_level: str | None = None,
) -> dict:
    """
    Ambil riwayat prediksi dengan paginasi dan filter opsional.

    Args:
        session      : Sesi database async
        page         : Nomor halaman (mulai dari 1)
        size         : Jumlah item per halaman
        filter_city  : (Opsional) Filter berdasarkan kota (cari di dalam array)
        filter_level : (Opsional) Filter berdasarkan level jabatan

    Returns:
        dict berisi metadata paginasi dan list items
    """
    # Base query conditions
    conditions = []

    if filter_city:
        # Cari row yang array 'city' mengandung nilai filter_city
        conditions.append(
            PredictionHistory.city.any(filter_city.lower())
        )

    if filter_level:
        # Cari row yang array 'job_level' mengandung nilai filter_level
        conditions.append(
            PredictionHistory.job_level.any(filter_level.lower())
        )

    # Hitung total data (dengan filter)
    count_query = select(func.count(PredictionHistory.id))
    for cond in conditions:
        count_query = count_query.where(cond)

    total_result = await session.execute(count_query)
    total_data = total_result.scalar_one()

    total_pages = max(1, math.ceil(total_data / size))

    # Ambil data sesuai halaman (dengan filter)
    offset = (page - 1) * size
    data_query = (
        select(PredictionHistory)
        .order_by(desc(PredictionHistory.created_at))
        .offset(offset)
        .limit(size)
    )
    for cond in conditions:
        data_query = data_query.where(cond)

    result = await session.execute(data_query)
    items = result.scalars().all()

    return {
        "total_data": total_data,
        "total_pages": total_pages,
        "current_page": page,
        "page_size": size,
        "items": items,
    }

async def get_history_by_id(session: AsyncSession, history_id: int) -> PredictionHistory | None:
    result = await session.execute(
        select(PredictionHistory).where(PredictionHistory.id == history_id)
    )
    return result.scalar_one_or_none()

async def update_actual_salaries(
    session: AsyncSession,
    history_id: int,
    actual_salaries: list[float],
) -> PredictionHistory:
    """
    Update gaji aktual (feedback) untuk sebuah record prediksi.

    Validasi:
    - Record harus ada
    - Panjang actual_salaries harus sama dengan data_count

    Returns:
        Record yang sudah diupdate
    """
    record = await get_history_by_id(session, history_id)

    if record is None:
        raise ValueError(f"History dengan ID {history_id} tidak ditemukan")

    if len(actual_salaries) != record.data_count:
        raise ValueError(
            f"Jumlah gaji aktual ({len(actual_salaries)}) harus sama dengan "
            f"jumlah data prediksi ({record.data_count})"
        )

    record.actual_salaries = actual_salaries
    await session.commit()
    await session.refresh(record)

    return record