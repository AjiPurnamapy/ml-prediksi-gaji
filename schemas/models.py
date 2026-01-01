from pydantic import BaseModel, Field

class SalaryInput(BaseModel):
    years_experience: float = Field(gt=0, le=50, description="Pengalaman kerja dalam tahun")

class SalaryOutput(BaseModel):
    input_years: float
    estimated_salary_million: float
    message: str