import joblib
import numpy as np
import logging
import sys

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from schemas.models import SalaryInput, SalaryOutput

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🔄 Loading model ML...")
    try:
        ml_models["gaji_model"] = joblib.load("gaji_model.pkl")
        logger.info("✅ Model berhasil di load ke memori!, dan Siap melayani request")
    except FileNotFoundError:
        logger.error("❌: Error: File 'gaji_model.pkl' tidak ditemukan. jalankan train_model.py dulu!")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌: Error loading model: {e}")
        sys.exit(1)
    yield 

    logger.info("🛑 Aplikasi berhenti. Membersihkan resource...")
    ml_models.clear()

app = FastAPI(
    title="API prediksi gaji",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
def read_root():
    return {"message": "Selamat datang di API Prediksi Gaji"}

@app.post("/predict", response_model=SalaryOutput)
def predict_salary(data: SalaryInput):
    if "gaji_model"not in ml_models or ml_models["gaji_model" is None]:
        logger.critical("Model hilang dari memori runtime!")
        raise HTTPException(status_code=500, detail="Model machine learning tidak aktif")
    try:
        years = data.years_experience
        input_data = np.array([[years]])
        prediction = ml_models["gaji_model"].predict(input_data)
        result_salary = prediction[0]

        logger.info(f"Prediksi: {years} Tahun -> {result_salary:.2f} Juta")

        return {
            "input_years": years,
            "estimated_salary_million":round(result_salary, 2),
            "message": "Prediksi berhasil dihitung menggunakan linear regression"
        }
    except Exception as e:
        logger.error(f"Error saat prediksi: {e}")
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal saat memproses data")
