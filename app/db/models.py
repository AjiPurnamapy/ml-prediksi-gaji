from datetime import datetime
from typing import List
from sqlalchemy import Integer, Float, DateTime, ARRAY, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base

class PredictionHistory(Base):
    """
    Table Untuk Menyimpan history setiap prediksi yang masuk
    """

    __tablename__ = "prediction_history"

    id: Mapped[int] = mapped_column(primary_key=True)

    # ARRAY(Float) = tipe data PostgreSQL untuk menyimpan list of float
    # Contoh: {2.6, 3.0, 5.0} tersimpan sebagai satu kolom
    input_years : Mapped[List[float]] = mapped_column(ARRAY(Float), nullable=False)
    converted_years : Mapped[List[float]] = mapped_column(ARRAY(Float), nullable=False)
    predicted_salaries : Mapped[List[float]] = mapped_column(ARRAY(Float), nullable=False)

    # Jumlah data dalam satu request — berguna untuk filtering
    data_count : Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    model_version : Mapped[str] = mapped_column(nullable=False)

    __table_args__ = (
        Index("idx_prediction_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<PredictionHistory id={self.id} "
            f"count={self.data_count} "
            f"at={self.created_at}> "
        )