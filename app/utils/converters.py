def convert_ym_to_years(ym: float) -> float:
    """
    Konversi format Y.M (TAHUN.BULAN) ke desimal murni.
    """
    if ym < 0:
        raise ValueError(f"Pengalaman tidak boleh negatif: '{ym}'.")
    
    # Parse via string untuk hindari floating point trap
    # str(2.11) → "2.11" → split(".") → ["2", "11"]
    parts = str(ym).split(".")
    years = int(parts[0])
    months_str = parts[1] if len(parts) > 1 else "0"
    months = int(months_str)   # "06" → 6, "11" → 11

    # Validasi hanya boleh 1 digit desimal
    if months >= 12:
        raise ValueError(
            f"Format tidak valid: '{ym}'. "
            f"Bulan harus antara 0-11, dapat: {months}."
            f"Contoh: 2.6 (6 bulan), bukan 2.11"
        )
    
    # Konversi ke desimal: tahun + (bulan / 12)
    return round(years + months / 12, 4)