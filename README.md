    import numpy as np                                  # standart industri untuk manipulasi array numerik yang efisien
    from sklearn.linear_model import LinearRegression   # algoritma linear regressiondari scikit-lear
    import joblib                                       # library standar untuk menyimpan (serialize) objek python/model ke file

    def main():
    # persiapan data (dummy)
    # di proyek nyata, data ini diambil dari database (postgresql) atau via pandas
    # X = fitur (inpput), y = target (output)

    # X_train: tahun pengalaman
    # menggunakan numpy array karena scikit-lear bekerja lebih cepat dengan format ini
    # .reshape(-1, 1) PENTING: scikit-learn mengharuskan input fitur berbentuk 2D array (Baris, Kolom)
    # -1 artinya "Biarkan numpy hitung jumlah barisnya", 1 artinya "harus 1 kolom"
    X_train = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]).reshape(-1, 1)             # .reshape() akan membuat data menurun ke bawah
    X_train = np.array([[1], [2], [3], [4], [5], [6], [7], [8], [9], [10], [11], [12]])    # ATAUPUN BISA TANPA MENGGUNAKAN .reshape(-1, 1)  # tinggal pilih ingin menggunakan yg mana

    # y_train: gaji (dalam jutaan/ribuan/ratusan).
    # target biasanya berbentuk 1D array (vektor), jadi tidak perlu reshape
    y_train = np.array([2.3, 3.4, 4.1, 5.8, 6.1, 7.9, 8.2, 9.9, 10, 11.2, 12.5, 13.5])

    print("DATA SIAP. MEMULAI TRAINING....")

    # INISIALISASI & TRAINIGN MODEL
    model = LinearRegression() # membuat instance model kosong (belum pintar)

    # .fit() adalah proses "belajar"
    # model mencari pola metematika antara X_train dan y_train.
    # di belakang layar, ini menggunakan matematika OLS (Ordinary least squares)
    model.fit(X_train, y_train)

    print("TRAINING SELESAI")

    # evaluasi sederhana (tes logic)
    # kita coba prediksi untuk penglaman 5 tahun (harusnya mendekati 7.0)
    sample_input = np.array([[1]])
    prediksi = model.predict(sample_input)

    print(f"TEST PREDIKSI: {sample_input[0]} TAHUN PENGALAMAN -> GAJI {prediksi[0]:.2f} JUTA")

    # cek "kecerdasan" model (koefisien)
    # coef_ adalah seberapa besar kenaikan gaji tiap tahun tambah pengalaman
    print(f"INSIGHT MODEL: SETIAP TAMBAH 1 TAHUN GAJI NAIK SEKITAR {model.coef_[0]:.2f} JUTA")

    # menyimpan model (serialization)
    # simpan "otak" model yang sudah pintar ke file fisik
    # file ini nanti yang akan di load oleh FastAPI
    filename = "gaji_model.pkl"
    joblib.dump(model, filename)
    print(f"MODEL DISIMPAN KE FILE '{filename}'. SIAP DIPAKAI DI FASTAPI!")

    if __name__ == "__main__":
        main()

DATA .reshape() akan terlihat seperti ini, data X_train harus berbentuk kolom yang menurun kebawah, kenapa y_train tidak? karena itu hanya berisi deretan angka jawaban dan tidak harus juga menurun kebawah.
[
 [1],
 [2], 
 [3],
 [4],
 [5],
 [6],
 [7],
 [8],
 [9],
 [10],
 [11],
 [12],
]
