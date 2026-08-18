from backend.database.connection import engine
from backend.database.models import Base


def init_db() -> None:
    """
    Create all database tables for the active database.

    The active database is selected by connection.py:
        - Cloud SQL PostgreSQL when Cloud SQL variables are set
        - DATABASE_URL when supplied
        - Local SQLite otherwise
    """

    print()
    print("Initializing Liquidity Monitor database")
    print("========================================")

    print(
        f"Database: "
        f"{engine.url.render_as_string(hide_password=True)}"
    )

    Base.metadata.create_all(
        bind=engine
    )

    print()
    print("Database schema initialized successfully.")


if __name__ == "__main__":
    init_db()