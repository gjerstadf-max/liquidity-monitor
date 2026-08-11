from backend.database.connection import DATABASE_PATH, engine
from backend.database.models import Base


def initialize_database() -> None:
    print("Creating Liquidity Monitor database...")
    print(f"Database location: {DATABASE_PATH}")

    Base.metadata.create_all(bind=engine)

    print("Database tables created successfully.")


if __name__ == "__main__":
    initialize_database()