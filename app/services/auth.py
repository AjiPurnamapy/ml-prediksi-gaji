"""
app/services/auth.py — Service autentikasi JWT

Berisi:
- Hashing & verifikasi password (bcrypt langsung)
- Generate & decode JWT token
- Dependency `get_current_user` untuk melindungi endpoint
- Dependency `require_admin_role` untuk endpoint admin-only
"""

import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import User

load_dotenv()

# --- Konfigurasi ---
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Token berlaku 1 jam

# --- Password Hashing ---
def hash_password(password: str) -> str:
    """Hash password menggunakan bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifikasi password plain terhadap hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

# --- JWT Token ---
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Generate JWT token.
    
    Args:
        data: Payload (biasanya {"sub": username})
        expires_delta: Durasi kadaluwarsa (default: ACCESS_TOKEN_EXPIRE_MINUTES)
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- OAuth2 Scheme ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# --- Dependencies ---
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency: Ekstrak user dari JWT token.
    Dipakai sebagai `Depends(get_current_user)` di endpoint yang dilindungi.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau sudah kadaluwarsa",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user

async def require_admin_role(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency: hanya mengizinkan user dengan role 'admin'.
    Dipakai untuk endpoint sensitif seperti /admin/retrain.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak. Endpoint ini hanya untuk admin.",
        )
    return current_user
