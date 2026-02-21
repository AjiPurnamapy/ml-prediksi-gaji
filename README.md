# 🎯 API Prediksi Gaji

API Machine Learning untuk memprediksi estimasi gaji berdasarkan pengalaman kerja, dibangun dengan FastAPI + scikit-learn.

---

## 📁 Struktur Project

```
salary-api/
├── app/                        ← Package utama aplikasi
│   ├── main.py                 ← Entry point FastAPI (routes & setup)
│   ├── schemas/
│   │   └── models.py           ← Pydantic models (validasi data)
│   ├── services/
│   │   └── predictor.py        ← Business logic ML
│   └── utils/
│       └── converters.py       ← Utility (konversi format Y.M)
├── ml/
│   ├── train_model.py          ← Script training model
│   └── gaji_model.pkl          ← Model hasil training (auto-generated)
├── tests/
│   └── test_utils.py           ← Unit tests
├── simulate_backend.py         ← Simulasi klien API
├── requirements.txt
└── README.md
```

---

## 🚀 Cara Menjalankan

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Training model (wajib pertama kali)
```bash
python ml/train_model.py
```

### 3. Jalankan server
```bash
uvicorn app.main:app --reload
```

### 4. Buka dokumentasi API
```
http://127.0.0.1:8000/docs
```

### 5. (Opsional) Jalankan simulasi klien
```bash
python simulate_backend.py
```

### 6. Jalankan tests
```bash
pytest tests/ -v
```

---

## 📡 Endpoint API

| Method | URL        | Deskripsi                    |
|--------|------------|------------------------------|
| GET    | `/`        | Info aplikasi                |
| GET    | `/health`  | Cek status server & model    |
| POST   | `/predict` | Prediksi gaji (endpoint utama) |

### Contoh Request POST /predict

```json
{
  "years_experience": [1.0, 2.6, 3.0, 5.9]
}
```

### Contoh Response

```json
{
  "input_years": [1.0, 2.6, 3.0, 5.9],
  "converted_years_decimal": [1.0, 2.5, 3.0, 5.75],
  "estimated_salary_million": [3.45, 4.71, 5.21, 7.89],
  "message": "Berhasil memprediksi 4 data sekaligus!"
}
```

---

## 📖 Format Input Y.M

Input menggunakan format **Tahun.Bulan**:

| Input | Artinya       | Konversi ke desimal |
|-------|---------------|---------------------|
| `2.6` | 2 thn 6 bln   | 2.5 tahun           |
| `3.0` | 3 tahun tepat | 3.0 tahun           |
| `1.3` | 1 thn 3 bln   | 1.25 tahun          |
| `0.6` | 6 bulan       | 0.5 tahun           |

> ⚠️ Digit desimal mewakili **BULAN** (0-11), bukan pecahan tahun!

---

## 🗺️ Roadmap

- [x] **Fase 1**: API dasar + validasi + struktur bersih
- [ ] **Fase 2**: PostgreSQL (simpan history prediksi)  
- [ ] **Fase 3**: Fitur ML tambahan (kota, pendidikan, jabatan)
- [ ] **Fase 4**: Docker & deployment