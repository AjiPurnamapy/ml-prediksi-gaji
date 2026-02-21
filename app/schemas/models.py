from pydantic import BaseModel, Field, field_validator
from typing import List
from app.utils.converters import convert_ym_to_years


class SalaryInput(BaseModel):
    """
    Schema untuk REQUEST body (data yang dikirim user ke API).
    FastAPI otomatis validasi setiap request masuk menggunakan class ini.
    """
    years_experience: List[float] = Field(
        ...,
        examples= [[1.0, 2.5, 3.11, 4.5]],
        description= ("List pengalaman kerja dalam format Tahun.Bulan (Y.M). "
            "Contoh: 2.6 = 2 tahun 6 bulan, 3.0 = 3 tahun tepat. "
            "PENTING: digit desimal adalah BULAN, bukan pecahan tahun."
        )
    )

    @field_validator("years_experience")
    @classmethod
    def validate_experience(cls, values: List[float]) -> List[float]:
        """
        Validasi aturan bisnis untuk input pengalaman kerja.
        Kalau ada yang gagal, Pydantic akan kirim HTTP 422 + pesan error ke user.
        """
        
        if not values:
            raise ValueError("List tidak boleh kosong")
        
        if len(values) > 100 :
            raise ValueError("Maksimal 100 data per request")
        
        for val in values:
            convert_ym_to_years(val)
            if val > 50:
                raise ValueError(
                    f"Nilai '{val}' tidak wajar. Maksimal 50 tahun pengalaman"
                )
        return values

class SalaryOutput(BaseModel):
    """
    Schema untuk RESPONSE (data yang dikembalikan API ke user).
    FastAPI otomatis filter & format response sesuai class ini.
    Kalau ada field ekstra di dict yang kamu return, FastAPI akan abaikan.
    """

    input_years: List[float]
    converted_years_decimal: List[float]
    estimated_salary_million: List[float]
    message: str

class HealthOutput(BaseModel):
    """Schema untuk endpoint /health — cek status server."""
    status: str
    model_loaded: bool
    version: str