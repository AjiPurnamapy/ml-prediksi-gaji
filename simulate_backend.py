import httpx
import json

BASE_URL = "http://127.0.0.1:8000"
PREDICT_URL = f"{BASE_URL}/predict"
HEALTH_URL = f"{BASE_URL}/health"

def cek_health_server() -> bool:
    """
    Cek apakah server hidup dan model ML sudah dimuat.
    Return True kalau server OK, False kalau ada masalah.
    """
    print("\n Mengecek Status server ...")
    try:
        response = httpx.get(HEALTH_URL, timeout=5.0)
        data = response.json()

        print(f"   Status      : {data['status']}")
        print(f"   Model loaded: {data['model_loaded']}")
        print(f"   Version     : {data['version']}")

        return data["status"] == "ok"
    
    except httpx.ConnectError:
        print("❌ Server tidak bisa dihubungi!")
        print("   Pastikan sudah menjalankan: uvicorn app.main:app --reload")
        return False

def hitung_prediksi_gaji(list_pengalaman: list[float]) -> list[float] | None:
    payload ={
        "years_experience": list_pengalaman
    }
    print(f"\n📤 Mengirim request ke {PREDICT_URL}")
    print(f"   Payload: {json.dumps(payload)}")

    try:
        response = httpx.post(PREDICT_URL, json=payload, timeout=10.0)
        print(f"   Status HTTP : {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            # Tampilkan detail response
            print(f"   Message     : {data['message']}")
            print("\n📥 Detail hasil:")
            print(f"   {'Input (Y.M)':<15} {'Konversi (thn)':<18} {'Prediksi Gaji'}")
            print(f"   {'-'*50}")

            for i, (input_ym, converted, salary) in enumerate(zip(
                data["input_years"],
                data["converted_years_decimal"],
                data["estimated_salary_million"]
            )):
                print(f"   {input_ym:<15} {converted:<18} Rp {salary:.2f} juta")
            return data["estimated_salary_million"]
        
        elif response.status_code == 422:
            # 422 = Unprocessable Entity (validasi gagal)
            error_detail = response.json().get("detail", "Unknown error")
            print(f"❌ Validasi gagal (422): {error_detail}")
            return None
        
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return None
        
    except httpx.ConnectError:
        print("GAGAL connect! pastikan server API ML (Uvicorn) sudah nyala")
        return None
    except httpx.TimeoutException:
        print("Request Timeout! Server terlalu lama merespons.")
        return None
    except Exception as e:
        print(f"Error tidak dikenal: {e}")
        return None

def demo_validasi_error():
    """
    Demonstrasi bagaimana API menangani input yang tidak valid.
    Berguna untuk testing dan dokumentasi.
    """
    print("\n" + "=" * 55)
    print("  DEMO: VALIDASI ERROR HANDLING")
    print("=" * 55)

    kasus_error = [
        {
            "deskripsi": "Format bulan tidak valid (2.13 → bulan ke-13)",
            "input": [2.13]
        },
        {
            "deskripsi": "Nilai negatif",
            "input": [-1.0]
        },
        {
            "deskripsi": "List kosong",
            "input": []
        },
    ]
    for kasus in kasus_error:
        print(f"\n🧪 Test: {kasus['deskripsi']}")
        print(f"   Input: {kasus['input']}")
        try:
            response = httpx.post(
                PREDICT_URL,
                json={"years_experience": kasus["input"]},
                timeout=5.0
            )
            print(f"   HTTP {response.status_code}: {response.json().get('detail', response.text)}")
        except Exception as e:
            print(f"   Error: {e}")

if __name__ == "__main__":
    print("=" * 55)
    print("  SIMULASI KLIEN API PREDIKSI GAJI")
    print("=" * 55)

    # Step 1: Cek server dulu sebelum kirim data
    if not cek_health_server():
        exit(1)  # Keluar kalau server tidak siap

    # Step 2: Skenario realistis
    print("\n" + "=" * 55)
    print("  SKENARIO: BATCH PREDIKSI UNTUK 5 KANDIDAT")
    print("=" * 55)

    kandidat = {
        "Budi (fresh graduate)": 0.6,       # 0 tahun 6 bulan
        "Sari (junior)": 2.3,               # 2 tahun 3 bulan
        "Andi (mid-level)": 4.0,            # 4 tahun tepat
        "Dewi (senior)": 7.6,               # 7 tahun 6 bulan
        "Pak Budi (principal)": 12.0,       # 12 tahun
    }

    nama_list = list(kandidat.keys())
    pengalaman_list = list(kandidat.values())

    hasil = hitung_prediksi_gaji(pengalaman_list)

    if hasil:
        print("\n💼 Ringkasan untuk HR:")
        print(f"   {'Nama':<30} {'Pengalaman':<15} {'Est. Gaji'}")
        print(f"   {'-'*55}")
        for nama, pengalaman, gaji in zip(nama_list, pengalaman_list, hasil):
            print(f"   {nama:<30} {pengalaman} thn         Rp {gaji:.1f} juta")

        print("\n✅ Data siap untuk disimpan ke database PostgreSQL!")
        print("   (Fitur ini akan kita tambahkan di Fase 2)")

    # Step 3: Demo error handling
    demo_validasi_error()

    print("\n✅ Simulasi selesai!")