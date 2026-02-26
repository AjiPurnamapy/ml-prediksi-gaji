import joblib
import logging
import os
import sys
import sentry_sdk

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.schemas.models import (
    SalaryInputV2, SalaryOutputV2, HealthOutput, HistoryOutput,
    PaginatedHistoryOutput, UserCreate, UserResponse, Token, FeedbackInput,
)
from app.services.predictor import predict_salaries_v2
from app.services.history import save_prediction, get_all_history, get_history_by_id, update_actual_salaries
from app.services.auth import (
    hash_password, verify_password, create_access_token, get_current_user,
)
from app.db.database import get_db, engine, Base
from app.db.models import User


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

ml_models = {}
APP_VERSION = "4.0.0"
MODEL_VERSION = "salary-linear-v2"

# --- Sentry (Error Tracking) ---
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=0.3,
        environment=os.getenv("APP_ENV", "development"),
        release=f"salary-api@{APP_VERSION}",
    )
    logging.getLogger(__name__).info("✅ Sentry error tracking aktif!")
else:
    logging.getLogger(__name__).info("ℹ️  SENTRY_DSN tidak diset — error tracking nonaktif.")

# --- Rate Limiter ---
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🔄 Menginisialisasi database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Tabel database siap!")

    # Load Model ML
    logger.info("🔄 Loading model ML V2...")
    try:
        ml_models["gaji_model_v2"] = joblib.load("ml/gaji_model_v2.pkl")
        logger.info("✅ Model V2 berhasil di-load ke memori! Siap melayani request.")
    except FileNotFoundError:
        logger.error("❌ File 'ml/gaji_model_v2.pkl' tidak ditemukan. Jalankan train_model_v2.py dulu!")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error loading model: {e}")
        sys.exit(1)
    yield 

    # Shutdown
    logger.info("🛑 Aplikasi berhenti. Membersihkan resource...")
    ml_models.clear()


app = FastAPI(
    title="API Prediksi Gaji V2",
    description=(
        "API untuk memprediksi estimasi gaji berdasarkan pengalaman kerja, kota, dan level jabatan. "
        "Menggunakan model pipeline (OneHotEncoder + LinearRegression) yang dilatih dengan data sintetik. "
        "Format input pengalaman: Y.M (Tahun.Bulan), contoh: 2.6 = 2 tahun 6 bulan. "
        "Semua endpoint prediksi dan history memerlukan JWT token."
    ),
    version=APP_VERSION,
    lifespan=lifespan,
)

# Pasang Rate Limiter sebagai middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# =====================================
#   INFO ENDPOINTS (Publik)
# =====================================

@app.get("/", tags=["Info"])
def read_root():
    """
    Endpoint sederhana untuk konfirmasi server hidup.
    Tidak butuh model ML, tidak butuh auth — hanya salam pembuka.
    """
    return {
        "message": "Selamat datang di API Prediksi Gaji V2",
        "version": APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }

@app.get("/health", response_model=HealthOutput, tags=["Info"])
def health_check():
    """
    Endpoint untuk monitoring — cek apakah server dan model dalam kondisi baik.
    """
    model_loaded = "gaji_model_v2" in ml_models and ml_models["gaji_model_v2"] is not None
    
    return {
        "status": "ok" if model_loaded else "degraded",
        "model_loaded": model_loaded,
        "version": APP_VERSION,
    }

# =====================================
#   AUTH ENDPOINTS (Publik)
# =====================================

@app.post("/register", response_model=UserResponse, status_code=201, tags=["Auth"])
async def register_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Registrasi user baru.
    Username harus unik, password minimal 6 karakter.
    """
    # Cek apakah username sudah terpakai
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Username '{data.username}' sudah terdaftar"
        )

    user = User(
        username=data.username,
        hashed_password=hash_password(data.password),
        role="user",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"✅ User baru terdaftar: {user.username}")
    return user

@app.post("/token", response_model=Token, tags=["Auth"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Login dan dapatkan JWT token.
    Gunakan form-data dengan field `username` dan `password`.
    Token berlaku selama 60 menit.
    """
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Username atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})
    logger.info(f"🔑 User '{user.username}' berhasil login")
    return {"access_token": access_token, "token_type": "bearer"}

# =====================================
#   PREDIKSI ENDPOINT (Dilindungi JWT + Rate Limit)
# =====================================

@app.post("/predict", response_model=SalaryOutputV2, tags=["Prediksi"])
@limiter.limit("20/minute")
async def predict_salary(
    request: Request,
    data: SalaryInputV2,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint utama: prediksi gaji berdasarkan pengalaman kerja, kota, dan level jabatan.
    Mendukung batch processing (banyak orang sekaligus).

    **Memerlukan JWT token** (header: `Authorization: Bearer <token>`).
    **Rate limit**: 20 request per menit per IP.
    """
    
    if "gaji_model_v2" not in ml_models or ml_models["gaji_model_v2"] is None:
        logger.critical("Model V2 hilang dari memori runtime!")
        raise HTTPException(
            status_code=500,
            detail="Model machine learning tidak aktif"
        )
    try:
        result = await run_in_threadpool(
            predict_salaries_v2,
            ml_models["gaji_model_v2"],
            data.years_experience,
            data.city,
            data.job_level
        )

        try:
            await save_prediction(
                session=db,
                prediction_result=result,
                model_version=MODEL_VERSION,
            )
        except Exception as db_err:
            logger.error(f"Gagal menyimpan histori ke DB: {db_err}")
            
        return result

    except ValueError as e:
        logger.warning(f"Input tidak valid: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error saat prediksi: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Terjadi kesalahan internal saat memproses data"
        )

# =====================================
#   HISTORY ENDPOINTS (Dilindungi JWT)
# =====================================

@app.get("/history", response_model=PaginatedHistoryOutput, tags=["History"])
async def get_history(
    page: int = 1,
    size: int = 10,
    city: str | None = None,
    job_level: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ambil riwayat prediksi dengan paginasi dan filter opsional.
    **Memerlukan JWT token**.

    - **page**: Nomor halaman (mulai dari 1)
    - **size**: Jumlah item per halaman (default 10, maks 100)
    - **city**: (Opsional) Filter berdasarkan kota, contoh: `?city=jakarta`
    - **job_level**: (Opsional) Filter berdasarkan level, contoh: `?job_level=senior`
    """
    if page < 1:
        raise HTTPException(status_code=422, detail="Parameter 'page' harus >= 1")
    if size < 1 or size > 100:
        raise HTTPException(status_code=422, detail="Parameter 'size' harus antara 1-100")

    result = await get_all_history(
        db, page=page, size=size,
        filter_city=city, filter_level=job_level,
    )
    return result

@app.get("/history/{history_id}", response_model=HistoryOutput, tags=["History"])
async def get_history_detail(
    history_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ambil detail satu riwayat prediksi berdasarkan ID.
    **Memerlukan JWT token**.
    """
    record = await get_history_by_id(db, history_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"History dengan ID {history_id} tidak ditemukan!"
        )
    return record

# =====================================
#   FEEDBACK ENDPOINT (Dilindungi JWT)
# =====================================

@app.put("/history/{history_id}/feedback", response_model=HistoryOutput, tags=["History"])
async def submit_feedback(
    history_id: int,
    data: FeedbackInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit gaji aktual (feedback) untuk sebuah prediksi yang sudah tersimpan.
    **Memerlukan JWT token**.

    Berguna untuk Active Learning — mengukur akurasi model AI
    terhadap gaji yang sesungguhnya disepakati.
    """
    try:
        record = await update_actual_salaries(
            session=db,
            history_id=history_id,
            actual_salaries=data.actual_salaries,
        )
        logger.info(f"📝 Feedback diterima untuk history #{history_id} oleh {current_user.username}")
        return record
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))