import numpy as np
import logging
from app.utils.converters import convert_ym_to_years

logger = logging.getLogger(__name__)

def predict_salaries(model, years_list: list[float]) -> dict:
    """
    Fungsi utama: terima list pengalaman kerja, kembalikan prediksi gaji.

    Flow di dalam fungsi ini:
    1. Konversi format Y.M → desimal murni
    2. Bentuk numpy array yang benar untuk scikit-learn
    3. Jalankan prediksi
    4. Rapikan hasil jadi list of float

    Args:
        model     : objek model scikit-learn yang sudah di-load
        years_list: list pengalaman dalam format Y.M (contoh: [2.6, 3.0])

    Returns:
        dict berisi input asli, hasil konversi, dan hasil prediksi

    Raises:
        Exception: diteruskan ke caller (main.py akan tangkap dan return HTTP 500)
    """

    # Konversi format Y.M → desimal
    converted = [convert_ym_to_years(ym) for ym in years_list]

    logger.info(f"Konversi Y.M Selesai: {years_list} -> {converted}")

    # np.array(converted)  → array 1D: [2.5, 3.08, 5.0]
    input_array = np.array(converted).reshape(-1, 1)

    # model.predict() butuh 2D array dan return numpy array
    raw_predictions = model.predict(input_array)

    # Rapihkan hasil
    # Ubah numpy array → list of float biasa (agar bisa di-serialize ke JSON)
    result = [round(float(x), 2) for x in raw_predictions]

    logger.info(f"Prediksi Selesai: {len(result)} data diproses")

    # Return semua data yang dibutuhkan oleh SalaryOutput schema
    return {
        "input_years": years_list,
        "converted_years_decimal": converted,
        "estimated_salary_million": result,
        "message": f"Berhasil memprediksi {len(result)} data sekaligus!"
    }
