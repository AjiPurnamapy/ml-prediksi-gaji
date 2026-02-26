from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
from datetime import datetime as dt
from app.utils.constants import VALID_CITIES, VALID_JOB_LEVELS


class SalaryInputV2(BaseModel):
    """
    Schema untuk REQUEST body (data yang dikirim user ke API).
    Mendukung batch processing — bisa kirim banyak orang sekaligus.

    Aturan validasi:
    1. Semua list harus panjangnya sama (1 orang = 1 elemen per list)
    2. years_experience: format Y.M, max 100 data, maks 50 tahun
    3. city: harus salah satu kota yang terdaftar
    4. job_level: harus salah satu level yang terdaftar
    """
    years_experience: List[float] = Field(
        ...,
        examples=[[3.5, 4.0]],
        description=(
            "List pengalaman kerja dalam format Tahun.Bulan (Y.M). "
            "Contoh: 2.6 = 2 tahun 6 bulan, 3.0 = 3 tahun tepat. "
            "PENTING: digit desimal adalah BULAN, bukan pecahan tahun."
        )
    )
    city: List[str] = Field(
        ...,
        examples=[["jakarta", "bandung"]],
        description=f"Kota lokasi kerja. Pilihan: {VALID_CITIES}"
    )
    job_level: List[str] = Field(
        ...,
        examples=[["junior", "senior"]],
        description=f"Level posisi pekerjaan. Pilihan: {VALID_JOB_LEVELS}"
    )

    @field_validator("years_experience")
    @classmethod
    def validate_experience(cls, values: List[float]) -> List[float]:
        """
        Validasi aturan bisnis: format Y.M, max 100 data, maks 50 tahun.
        Memanfaatkan convert_ym_to_years() untuk cek format bulan.
        """
        from app.utils.converters import convert_ym_to_years

        if not values:
            raise ValueError("List pengalaman tidak boleh kosong")

        if len(values) > 100:
            raise ValueError("Maksimal 100 data per request")

        for val in values:
            convert_ym_to_years(val)  # Akan raise ValueError jika format salah
            if val > 50:
                raise ValueError(
                    f"Nilai '{val}' tidak wajar. Maksimal 50 tahun pengalaman"
                )
        return values

    @field_validator("city")
    @classmethod
    def validate_city(cls, values: List[str]) -> List[str]:
        """Normalisasi dan validasi setiap kota."""
        validated = []
        for value in values:
            val_lower = value.strip().lower()
            if val_lower not in VALID_CITIES:
                raise ValueError(
                    f"Kota '{val_lower}' tidak valid. Pilih salah satu: {VALID_CITIES}"
                )
            validated.append(val_lower)
        return validated

    @field_validator("job_level")
    @classmethod
    def validate_job_level(cls, values: List[str]) -> List[str]:
        """Normalisasi dan validasi setiap level jabatan."""
        validated = []
        for value in values:
            val_lower = value.strip().lower()
            if val_lower not in VALID_JOB_LEVELS:
                raise ValueError(
                    f"Level '{val_lower}' tidak valid. Pilih salah satu: {VALID_JOB_LEVELS}"
                )
            validated.append(val_lower)
        return validated

    @model_validator(mode="after")
    def validate_equal_lengths(self) -> "SalaryInputV2":
        """
        Pastikan panjang semua list identik.
        1 orang = 1 elemen di setiap list.
        """
        lengths = {
            "years_experience": len(self.years_experience),
            "city": len(self.city),
            "job_level": len(self.job_level),
        }
        unique_lengths = set(lengths.values())

        if len(unique_lengths) > 1:
            detail = ", ".join(f"{k}={v}" for k, v in lengths.items())
            raise ValueError(
                f"Panjang semua list harus sama (1 orang = 1 elemen per list). "
                f"Saat ini: {detail}"
            )
        return self


class SalaryOutputV2(BaseModel):
    """
    Schema untuk RESPONSE — data prediksi yang dikembalikan API ke user.
    FastAPI otomatis filter & format response sesuai class ini.
    """

    input_years: List[float]
    city: List[str]
    job_level: List[str]
    converted_years_decimal: List[float]
    estimated_salary_million: List[float]
    message: str


class HealthOutput(BaseModel):
    """Schema untuk endpoint /health — cek status server."""
    status: str
    model_loaded: bool
    version: str


class HistoryOutput(BaseModel):
    """Schema untuk response endpoint /history — riwayat prediksi."""
    model_config = {"from_attributes": True}

    id: int
    input_years: List[float]
    converted_years: List[float]
    city: List[str] | None = None
    job_level: List[str] | None = None
    predicted_salaries: List[float]
    actual_salaries: Optional[List[float]] = None
    data_count: int
    model_version: str
    created_at: dt


class PaginatedHistoryOutput(BaseModel):
    """Schema response paginasi untuk endpoint /history."""
    total_data: int
    total_pages: int
    current_page: int
    page_size: int
    items: List[HistoryOutput]


class FeedbackInput(BaseModel):
    """Schema untuk mengirimkan gaji aktual (feedback) ke prediksi yang sudah tersimpan."""
    actual_salaries: List[float] = Field(
        ...,
        examples=[[4.5, 5.0, 8.0]],
        description="List gaji aktual (juta Rp) yang akhirnya disepakati saat kontrak."
    )

    @field_validator("actual_salaries")
    @classmethod
    def validate_salaries(cls, values: List[float]) -> List[float]:
        if not values:
            raise ValueError("List gaji aktual tidak boleh kosong")
        for val in values:
            if val <= 0:
                raise ValueError(f"Gaji aktual harus positif, dapat: {val}")
        return values


# --- Auth Schemas ---

class UserCreate(BaseModel):
    """Schema untuk registrasi user baru."""
    username: str = Field(..., min_length=3, max_length=50, examples=["admin_hr"])
    password: str = Field(..., min_length=6, max_length=100, examples=["rahasia123"])

class UserResponse(BaseModel):
    """Schema response setelah registrasi berhasil."""
    model_config = {"from_attributes": True}

    id: int
    username: str
    role: str
    created_at: dt

class Token(BaseModel):
    """Schema response setelah login berhasil."""
    access_token: str
    token_type: str = "bearer"
