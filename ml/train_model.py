import numpy as np     
from sklearn.linear_model import LinearRegression  
from sklearn.metrics import mean_absolute_error, r2_score
import joblib   
import os

def main():
    print("=" * 50)
    print("  TRAINING MODEL PREDIKSI GAJI")
    print("=" * 50)

    X_train = np.array([
        0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0,
        5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 9.0, 10.0, 11.0, 12.0
    ]).reshape(-1, 1)   # .reshape(-1, 1) → ubah dari [0.5, 1.0, ...] menjadi [[0.5], [1.0], ...]

    # y_train TIDAK di-reshape karena ini hanya deretan jawaban (1D sudah cukup)
    y_train = np.array([
        2.0, 2.3, 2.8, 3.4, 4.0, 4.1, 4.8, 5.8, 6.0, 6.1,
        6.9, 7.9, 8.0, 8.2, 9.0, 9.9, 10.0, 11.2, 12.5, 13.5
    ])

    print(f"✅ Data siap: {len(X_train)} sampel data training")
    print(f"   Rentang pengalaman: {X_train.min()} - {X_train.max()} tahun")
    print(f"   Rentang gaji      : {y_train.min()} - {y_train.max()} juta")

    print("\n🔄 MEMULAI TRAINING....")

    # LinearRegression() → buat objek model KOSONG (belum belajar apa-apa)
    model = LinearRegression() 
    model.fit(X_train, y_train)

    print("✅ TRAINING SELESAI")

    y_pred = model.predict(X_train)

    # MAE = rata-rata selisih antara prediksi vs jawaban sebenarnya
    # MAE = 0.3 artinya: rata-rata model meleset 0.3 juta = 300 ribu
    mae = mean_absolute_error(y_train, y_pred)

    # R² (R-squared) = seberapa baik model menjelaskan variasi data
    # R² = 1.0 → sempurna, R² = 0.0 → tidak lebih baik dari rata-rata
    # R² = 0.95 → model menjelaskan 95% variasi data ✅
    r2 = r2_score(y_train, y_pred)

    print("\n📊 Evaluasi Model:")
    print(f"   Koefisien (kenaikan gaji/tahun)  : {model.coef_[0]:.3f} juta")
    print(f"   Intercept (gaji awal)            : {model.intercept_:.3f} juta")
    print(f"   MAE (rata-rata error)            : {mae:.3f} juta = Rp {mae*1_000_000:,.0f}")
    print(f"   R² Score                         : {r2:.4f} ({r2*100:.1f}% akurasi)")

    test_case = [1.0, 3.0, 5.0, 10.0]
    print("\n TES PREDIKSI:")
    for tahun in test_case:
        hasil = model.predict([[tahun]])[0]
        print(f"   {tahun:4} tahun pengalaman → prediksi gaji: Rp {hasil:.2f} juta")

    # SIMPAN MODEL KE FILE
    # Pastikan folder ml/ ada
    os.makedirs("ml", exist_ok=True)

    # joblib.dump() = serialize objek Python → file binary (.pkl)
    output_path = "ml/gaji_model.pkl"
    joblib.dump(model, output_path)
    print(f"\n💾 Model disimpan ke '{output_path}'")
    print("   Jalankan server: python -m uvicorn app.main:app --reload")

if __name__ == "__main__":
    main()