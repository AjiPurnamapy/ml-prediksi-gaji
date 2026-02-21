"""
tests/test_utils.py — Unit test untuk utility functions

Cara jalankan:
    pytest tests/ -v

Kenapa testing penting?
→ Kalau kamu ubah kode converter nanti, test ini langsung kasih tahu
  kalau ada yang rusak — tanpa harus coba manual satu per satu.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.converters import convert_ym_to_years
from app.schemas.models import SalaryInput
from pydantic import ValidationError


class TestConvertYMToYears:
    """Kumpulan test untuk fungsi convert_ym_to_years."""

    def test_konversi_normal(self):
        """Test konversi angka yang valid."""
        assert convert_ym_to_years(2.6)  == 2.5    # 2 thn 6 bln
        assert convert_ym_to_years(3.0)  == 3.0    # 3 thn 0 bln
        assert convert_ym_to_years(1.3)  == 1.25   # 1 thn 3 bln

    def test_nol_bulan(self):
        """Tahun bulat (tanpa bulan) harus tetap sama."""
        assert convert_ym_to_years(5.0) == 5.0
        assert convert_ym_to_years(0.0) == 0.0

    def test_bulan_maksimal(self):
        """11 bulan adalah nilai bulan tertinggi yang valid."""
        result = convert_ym_to_years(2.11)
        assert result == pytest.approx(2 + 11/12, rel=1e-3)

    def test_format_bulan_tidak_valid(self):
        """Bulan >= 12 harus raise ValueError."""
        with pytest.raises(ValueError, match="Format bulan tidak valid"):
            convert_ym_to_years(2.12)   # bulan ke-12

        with pytest.raises(ValueError, match="Format bulan tidak valid"):
            convert_ym_to_years(1.15)   # bulan ke-15

    def test_nilai_negatif(self):
        """Nilai negatif harus raise ValueError."""
        with pytest.raises(ValueError, match="tidak boleh negatif"):
            convert_ym_to_years(-1.0)


class TestSalaryInputValidator:
    """Test untuk Pydantic validator di SalaryInput."""

    def test_input_valid(self):
        data = SalaryInput(years_experience=[1.0, 2.6, 3.0])
        assert len(data.years_experience) == 3

    def test_input_negatif_ditolak(self):
        with pytest.raises(ValidationError):
            SalaryInput(years_experience=[-1.0])

    def test_input_kosong_ditolak(self):
        with pytest.raises(ValidationError):
            SalaryInput(years_experience=[])

    def test_format_bulan_invalid_ditolak(self):
        with pytest.raises(ValidationError):
            SalaryInput(years_experience=[2.12])    # bulan ke-12