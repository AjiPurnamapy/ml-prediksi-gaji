"""
migrate_db.py — Skrip migrasi mini untuk menambahkan kolom baru ke tabel yang sudah ada.

Jalankan sekali saja setelah update model database:
    python migrate_db.py

Aman dijalankan berkali-kali (idempotent) — jika kolom sudah ada, akan di-skip.
"""

import asyncio
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from sqlalchemy import text
from app.db.database import engine

MIGRATIONS = [
    {
        "description": "Tambah kolom actual_salaries ke prediction_history",
        "check": "SELECT column_name FROM information_schema.columns WHERE table_name='prediction_history' AND column_name='actual_salaries'",
        "sql": "ALTER TABLE prediction_history ADD COLUMN actual_salaries FLOAT[] DEFAULT NULL",
    },
]

async def run_migrations():
    print("🔄 Menjalankan migrasi database...\n")

    async with engine.begin() as conn:
        for i, migration in enumerate(MIGRATIONS, 1):
            # Cek apakah kolom sudah ada
            result = await conn.execute(text(migration["check"]))
            exists = result.fetchone()

            if exists:
                print(f"   ✅ [{i}] SKIP — {migration['description']} (sudah ada)")
            else:
                await conn.execute(text(migration["sql"]))
                print(f"   🆕 [{i}] OK — {migration['description']}")

    print("\n✅ Migrasi selesai!")

if __name__ == "__main__":
    asyncio.run(run_migrations())
