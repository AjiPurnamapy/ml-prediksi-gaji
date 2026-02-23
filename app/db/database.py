import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()

# Bangun connection string dari variabel .env
# Format: postgresql+asyncpg://user:password@host:port/dbname
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

# Engine = "mesin" koneksi ke database
# echo=True → tampilkan SQL yang dieksekusi di terminal (berguna saat development)
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    echo=True,   # Ubah ke False jika Production ready
    max_overflow=20,
    pool_timeout=30
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False  # Objek tetap bisa diakses setelah commit
)

# Base class untuk semua tabel — semua model DB akan inherit dari ini
class Base(DeclarativeBase):
    pass

async def get_db():
    """
    Dependency function untuk FastAPI.
    Setiap request yang butuh DB akan dapat session baru,
    dan session otomatis ditutup setelah request selesai.

    Pakai 'yield' bukan 'return' agar FastAPI bisa cleanup
    session setelah request selesai (finally block).
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()