from datetime import datetime
from typing import List
from sqlalchemy import Integer, Float, DateTime, ARRAY, String, Index
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
    city : Mapped[List[str]] = mapped_column(ARRAY(String), nullable=True)
    job_level : Mapped[List[str]] = mapped_column(ARRAY(String), nullable=True)
    predicted_salaries : Mapped[List[float]] = mapped_column(ARRAY(Float), nullable=False)

    # Feedback Loop: gaji aktual yang disepakati saat kontrak (diisi oleh HR setelah proses hiring)
    actual_salaries : Mapped[List[float] | None] = mapped_column(ARRAY(Float), nullable=True)

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


class User(Base):
    """
    Tabel user untuk autentikasi JWT.
    Setiap user memiliki role (admin / user) untuk otorisasi endpoint.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username} role={self.role}>"