from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "liquidity.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


def ensure_data_directory() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


ensure_data_directory()


engine = create_engine(
    DATABASE_URL,
    echo=False,
)


SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    expire_on_commit=False,
)


def get_session() -> Session:
    return SessionLocal()