"""
ml/auto_retrain.py — Automated Active Learning (MLOps)

Skrip ini membaca data feedback (actual_salaries) dari database,
lalu melatih ulang model prediksi gaji menggunakan data asli tersebut.

Bisa dijalankan secara:
1. Manual: python ml/auto_retrain.py
2. Otomatis: via endpoint POST /admin/retrain (dipanggil dari main.py)

Model baru hanya akan menggantikan model lama jika MAE-nya lebih baik.
"""

import os
import sys
import asyncio
import numpy as np
import joblib
import logging

# Windows CMD Unicode patch
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Pastikan root project ada di sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sklearn.linear_model import Ridge
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score

from app.db.database import AsyncSessionLocal
from app.db.models import PredictionHistory
from app.utils.constants import VALID_CITIES, VALID_JOB_LEVELS

logger = logging.getLogger(__name__)

MODEL_V2_PATH = "ml/gaji_model_v2.pkl"
MODEL_V3_PATH = "ml/gaji_model_v3.pkl"


async def fetch_feedback_data() -> tuple[list, list]:
    """
    Ambil semua histori prediksi yang sudah memiliki feedback (actual_salaries).
    Kembalikan sebagai (X_rows, y_values) yang di-flatten.

    Contoh:
        1 record = 5 kandidat → jadi 5 baris training data
    """
    async with AsyncSessionLocal() as session:
        query = select(PredictionHistory).where(
            PredictionHistory.actual_salaries.is_not(None)
        )
        result = await session.execute(query)
        records = result.scalars().all()

    X_rows = []
    y_values = []

    for record in records:
        for i in range(record.data_count):
            years = record.converted_years[i]
            city = record.city[i] if record.city else "jakarta"
            level = record.job_level[i] if record.job_level else "mid"
            actual_salary = record.actual_salaries[i]

            X_rows.append([years, city, level])
            y_values.append(actual_salary)

    return X_rows, y_values


def build_retrain_pipeline() -> TransformedTargetRegressor:
    """
    Pipeline V3: Ridge regression (tahan overfitting) + Log transform.
    Sama arsitekturnya dengan V2 tapi pakai Ridge bukan LinearRegression.
    """
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "city_encoder",
                OneHotEncoder(
                    categories=[VALID_CITIES],
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
                [1],
            ),
            (
                "level_encoder",
                OneHotEncoder(
                    categories=[VALID_JOB_LEVELS],
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
                [2],
            ),
        ],
        remainder="passthrough",
    )

    inner_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", Ridge(alpha=1.0)),  # Ridge = L2 regularization
    ])

    model = TransformedTargetRegressor(
        regressor=inner_pipeline,
        func=np.log,
        inverse_func=np.exp,
    )

    return model


async def retrain_model() -> dict:
    """
    Proses utama retraining:
    1. Ambil data feedback dari database
    2. Latih model V3 (Ridge + Log transform)
    3. Bandingkan MAE dengan model V2
    4. Simpan model V3 hanya jika lebih baik

    Returns:
        dict berisi ringkasan hasil retraining
    """
    logger.info("🔄 Memulai proses retraining model...")

    # Step 1: Ambil data feedback
    X_rows, y_values = await fetch_feedback_data()
    feedback_count = len(y_values)

    if feedback_count < 10:
        msg = f"Data feedback belum cukup ({feedback_count} sampel, minimal 10)"
        logger.warning(f"⚠️ {msg}")
        return {
            "status": "skipped",
            "message": msg,
            "feedback_count": feedback_count,
        }

    X = np.array(X_rows, dtype=object)
    y = np.array(y_values, dtype=float)

    logger.info(f"📊 Data feedback: {feedback_count} sampel")

    # Step 2: Latih model V3
    model_v3 = build_retrain_pipeline()
    model_v3.fit(X, y)

    y_pred_v3 = model_v3.predict(X)
    mae_v3 = mean_absolute_error(y, y_pred_v3)
    r2_v3 = r2_score(y, y_pred_v3)

    logger.info(f"📈 Model V3 — MAE: {mae_v3:.3f} juta, R²: {r2_v3:.4f}")

    # Step 3: Bandingkan dengan model V2
    result = {
        "status": "completed",
        "feedback_count": feedback_count,
        "v3_mae": round(mae_v3, 4),
        "v3_r2": round(r2_v3, 4),
        "v2_mae": None,
        "model_replaced": False,
    }

    try:
        model_v2 = joblib.load(MODEL_V2_PATH)
        y_pred_v2 = model_v2.predict(X)
        mae_v2 = mean_absolute_error(y, y_pred_v2)
        result["v2_mae"] = round(mae_v2, 4)

        logger.info(f"📉 Model V2 — MAE: {mae_v2:.3f} juta (pada data feedback)")

        # Step 4: Replace hanya jika V3 lebih baik
        if mae_v3 < mae_v2:
            joblib.dump(model_v3, MODEL_V3_PATH)
            result["model_replaced"] = True
            result["message"] = (
                f"Model V3 lebih akurat! MAE turun dari {mae_v2:.3f} → {mae_v3:.3f} juta. "
                f"Model baru disimpan ke '{MODEL_V3_PATH}'."
            )
            logger.info(f"✅ {result['message']}")
        else:
            result["message"] = (
                f"Model V2 masih lebih baik (MAE V2={mae_v2:.3f} vs V3={mae_v3:.3f}). "
                f"Model V3 TIDAK disimpan."
            )
            logger.info(f"ℹ️ {result['message']}")

    except FileNotFoundError:
        # V2 tidak ada, langsung simpan V3
        joblib.dump(model_v3, MODEL_V3_PATH)
        result["model_replaced"] = True
        result["message"] = f"Model V2 tidak ditemukan. Model V3 disimpan ke '{MODEL_V3_PATH}'."
        logger.info(f"✅ {result['message']}")

    return result


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    print("=" * 55)
    print("  AUTO RETRAIN — ACTIVE LEARNING (MLOps)")
    print("=" * 55)

    result = asyncio.run(retrain_model())

    print(f"\n📋 Hasil Retraining:")
    for key, value in result.items():
        print(f"   {key}: {value}")

    print("\n" + "=" * 55)
