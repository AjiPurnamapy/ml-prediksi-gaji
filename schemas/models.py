from pydantic import BaseModel, Field
from typing import List

class SalaryInput(BaseModel):
    years_experience: List[float] = Field(..., examples=[1.0, 2.5, 3.0, 4.5], description="Masukkan pengalaman kerja dalam format Tahun.Bulan (Y.M)")

class SalaryOutput(BaseModel):
    input_years: List[float]
    estimated_salary_million: List[float]
    message: str