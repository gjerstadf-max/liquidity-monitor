from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker


load_dotenv()


PROJECT_ROOT = Path(
    __file__
).resolve().parents[2]

DATA_DIR = (
    PROJECT_ROOT
    / "data"
)

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

SQLITE_PATH = (
    DATA_DIR
    / "liquidity.db"
)


def _build_engine():
    """
    Build the database engine.

    Priority:

    1. Cloud SQL Unix socket
    2. DATABASE_URL
    3. Local SQLite

    Local development therefore continues to work
    without any database environment variables.
    """

    instance_socket = os.getenv(
        "INSTANCE_UNIX_SOCKET"
    )


    # =========================================================
    # CLOUD SQL POSTGRESQL
    # =========================================================

    if instance_socket:

        db_user = os.environ[
            "DB_USER"
        ]

        db_pass = os.environ[
            "DB_PASS"
        ]

        db_name = os.environ[
            "DB_NAME"
        ]


        database_url = URL.create(
            drivername="postgresql+pg8000",

            username=db_user,

            password=db_pass,

            database=db_name,

            query={
                "unix_sock": (
                    f"{instance_socket}"
                    "/.s.PGSQL.5432"
                )
            },
        )


        return create_engine(
            database_url,

            pool_pre_ping=True,

            pool_size=5,

            max_overflow=2,

            pool_recycle=1800,
        )


    # =========================================================
    # GENERIC DATABASE URL
    # =========================================================

    database_url = os.getenv(
        "DATABASE_URL"
    )

    if database_url:

        return create_engine(
            database_url,

            pool_pre_ping=True,

            pool_size=5,

            max_overflow=2,

            pool_recycle=1800,
        )


    # =========================================================
    # LOCAL SQLITE
    # =========================================================

    sqlite_url = (
        f"sqlite:///{SQLITE_PATH}"
    )


    return create_engine(
        sqlite_url,

        connect_args={
            "check_same_thread": False,
        },
    )


engine = _build_engine()


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_session():
    """
    Return a database session.

    Existing code can continue using:

        with get_session() as session:
            ...
    """

    return SessionLocal()