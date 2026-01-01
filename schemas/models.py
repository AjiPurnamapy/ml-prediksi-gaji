from pydantic import BaseModel, Field
from typing import Optional

class SalaryInput(BaseModel):
    years_experience: float

class SalaryOutput(BaseModel):
    input_years: float
    estimated_salary_million: float
    message: str