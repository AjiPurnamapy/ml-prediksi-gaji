import numpy as np
import joblib
from sklearn.linear_model import LinearRegression

def main():
    # input X_train: [Luas tanah (m2), jumlah kamar]
    X_train = np.array([
        [50, 2, 0], 
        [60, 3, 1],
        [70, 2, 1],
        [80, 4, 0],
        [100, 3, 1],
        [150, 5, 0],
        [40, 1, 0], 
        [200, 6, 1]
    ])
    # input y_train : harga rumah (dalam jutaan)
    y_train = np.array([300, 450, 500, 650, 800, 1200, 200, 1600])

    print("Data rumah siap (Luas & Kamar & garasi). Training dimulai...")

    model = LinearRegression()
    model.fit(X_train, y_train)

    print("Training Selesai")

    # evaluasi insight karena input ada 2, coef_ (bobot) juga akan ada 2 angka
    # coef_[0] = bobot luas tanah
    # coef_[1] = bobot jumlah kamar
    print(f"\n INSIGHT MODEL:")
    print(f"Harga dasar (intercept): {model.intercept_:.2f} Juta")
    print(f"Setiap tambah per m2 tanah, harga naik: {model.coef_[0]:.2f} Juta")
    print(f"Setiap tambah kamar, harga naik: {model.coef_[1]:.2f} Juta")
    print(f"Harga fitur garasi : Rp {model.coef_[2]:.2f} Juta")

    # tes prediksi
    sample_rumah = np.array([[300, 5, 1]])
    harga_prediksi = model.predict(sample_rumah)

    print(f"\n Prediksi rumah {sample_rumah[0]} (Luas, Kamar): Rp {harga_prediksi[0]:.2f} Juta")

    # simpan
    joblib.dump(model, "ml/house_model.pkl")
    print("Model disimpan sebagai 'house_model.pkl'")

if __name__ == "__main__":
    main()
