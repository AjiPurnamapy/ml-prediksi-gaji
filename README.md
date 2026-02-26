# 🎯 API Prediksi Gaji V2

API Machine Learning untuk memprediksi estimasi gaji berdasarkan **pengalaman kerja, kota, dan level jabatan** — dibangun dengan FastAPI + scikit-learn.

Dilengkapi dengan: JWT Authentication, Rate Limiting, Paginasi, Feedback Loop, Docker, CI/CD, dan Sentry Error Tracking.

---

## 📁 Struktur Project

```
salary-api/
├── .github/workflows/          ← CI/CD (GitHub Actions)
│   ├── pytest.yml              ← Auto-run test setiap push
│   └── docker-build.yml        ← Validasi Docker build
├── app/
│   ├── main.py                 ← Entry point FastAPI (routes & setup)
│   ├── schemas/
│   │   └── models.py           ← Pydantic models (validasi + auth schemas)
│   ├── services/
│   │   ├── predictor.py        ← Business logic ML
│   │   ├── history.py          ← Service histori (paginasi, filter, feedback)
│   │   └── auth.py             ← JWT auth (hashing, token, dependency)
│   ├── db/
│   │   ├── database.py         ← Koneksi PostgreSQL (async)
│   │   └── models.py           ← SQLAlchemy models (PredictionHistory, User)
│   └── utils/
│       ├── converters.py       ← Konversi format Y.M → desimal
│       └── constants.py        ← Daftar kota & level valid
├── ml/
│   ├── train_model_v2.py       ← Script training model V2 (log-transform)
│   └── gaji_model_v2.pkl       ← Model hasil training (gitignored)
├── tests/
│   └── test_utils.py           ← Unit tests (14 test cases)
├── simulate_backend.py         ← Simulasi klien API (dengan auth)
├── migrate_db.py               ← Migrasi database (idempotent)
├── Dockerfile                  ← Docker image (python:3.11-slim)
├── docker-compose.yml          ← Orchestration (web service + healthcheck)
├── .dockerignore
├── .env                        ← Kredensial (gitignored)
├── requirements.txt
└── README.md
```

---

## 🚀 Cara Menjalankan

### Opsi A: Lokal (Development)

```bash
# 1. Buat virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Konfigurasi .env
# Buat file .env berisi:
#   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/salary_db
#   JWT_SECRET_KEY=random-secret-key-yang-kuat
#   SENTRY_DSN=                  (opsional, kosongkan jika belum punya)

# 4. Training model (wajib pertama kali)
python ml/train_model_v2.py

# 5. Migrasi database (jika upgrade dari versi lama)
python migrate_db.py

# 6. Jalankan server
uvicorn app.main:app --reload

# 7. Buka dokumentasi API
# http://127.0.0.1:8000/docs
```

### Opsi B: Docker

```bash
# Build dan jalankan
docker-compose up --build

# Atau tanpa compose
docker build -t salary-api .
docker run -p 8000:8000 --env-file .env salary-api
```

### Testing

```bash
# Unit tests
pytest tests/ -v

# Simulasi end-to-end (server harus aktif)
python simulate_backend.py
```

---

## 📡 Endpoint API

### Publik (Tanpa Token)

| Method | URL          | Deskripsi                      |
|--------|--------------|--------------------------------|
| GET    | `/`          | Info aplikasi                  |
| GET    | `/health`    | Cek status server & model      |
| POST   | `/register`  | Registrasi user baru           |
| POST   | `/token`     | Login → dapat JWT token        |

### Dilindungi JWT (Header: `Authorization: Bearer <token>`)

| Method | URL                             | Deskripsi                         |
|--------|---------------------------------|-----------------------------------|
| POST   | `/predict`                      | Prediksi gaji (rate limit: 20/min)|
| GET    | `/history`                      | Riwayat prediksi (paginasi+filter)|
| GET    | `/history/{id}`                 | Detail satu prediksi              |
| PUT    | `/history/{id}/feedback`        | Submit gaji aktual (feedback)     |

### Contoh Request POST /predict

```json
{
  "years_experience": [1.0, 2.6, 5.0],
  "city": ["jakarta", "bandung", "surabaya"],
  "job_level": ["junior", "mid", "senior"]
}
```

### Contoh Query GET /history

```
GET /history?page=1&size=5&city=jakarta&job_level=senior
```

---

## 📖 Format Input Y.M

| Input | Artinya       | Konversi ke desimal |
|-------|---------------|---------------------|
| `2.6` | 2 thn 6 bln   | 2.5 tahun           |
| `3.0` | 3 tahun tepat | 3.0 tahun           |
| `1.3` | 1 thn 3 bln   | 1.25 tahun          |
| `0.6` | 6 bulan       | 0.5 tahun           |

> ⚠️ Digit desimal mewakili **BULAN** (0-11), bukan pecahan tahun!

---

## ⚙️ Environment Variables (.env)

| Variable         | Wajib | Deskripsi                               |
|------------------|-------|-----------------------------------------|
| `DATABASE_URL`   | ✅    | Connection string PostgreSQL (asyncpg)  |
| `JWT_SECRET_KEY` | ✅    | Secret key untuk signing JWT token      |
| `SENTRY_DSN`     | ❌    | DSN dari Sentry.io (error tracking)     |
| `APP_ENV`        | ❌    | Environment label (default: development)|

---

## 🗺️ Roadmap

- [x] **Phase 1**: Paginasi endpoint `/history`
- [x] **Phase 2**: Dockerization (`Dockerfile` + `docker-compose.yml`)
- [x] **Phase 3**: JWT Authentication (`/register`, `/token`)
- [x] **Phase 4**: Rate Limiting (20 req/min pada `/predict`)
- [x] **Phase 5**: Feedback Loop (`PUT /history/{id}/feedback`)
- [x] **Phase 6**: Advanced Filtering (`?city=...&job_level=...`)
- [x] **Phase 7**: CI/CD (GitHub Actions — pytest + docker build)
- [x] **Phase 8**: Centralized Logging (Sentry integration)