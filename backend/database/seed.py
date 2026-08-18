from sqlalchemy import select

from backend.database.connection import get_session
from backend.database.models import DataSource, Indicator


def seed_database() -> None:
    with get_session() as session:
        ny_fed = session.scalar(
            select(DataSource).where(
                DataSource.short_name == "NY Fed"
            )
        )

        if ny_fed is None:
            ny_fed = DataSource(
                name="Federal Reserve Bank of New York",
                short_name="NY Fed",
                website="https://www.newyorkfed.org/",
                is_primary=True,
            )
            session.add(ny_fed)
            session.flush()

            print("Added data source: NY Fed")
        else:
            print("Data source already exists: NY Fed")

        indicator_definitions = [
            {
                "symbol": "sofr",
                "name": "Secured Overnight Financing Rate",
                "category": "Funding",
                "frequency": "Daily",
                "units": "Percent",
            },
            {
                "symbol": "effr",
                "name": "Effective Federal Funds Rate",
                "category": "Funding",
                "frequency": "Daily",
                "units": "Percent",
            },

            {
                "symbol": "reserve_balances",
                "name": "Reserve Balances with Federal Reserve Banks",
                "category": "Funding",
                "frequency": "Daily",
                "units": "USD Billions",
            },
            {   
                "symbol": "tga",
                "name": "U.S. Treasury General Account",
                "category": "Funding",
                "frequency": "Daily",
                "units": "USD Billions",
            },

        ]

        for definition in indicator_definitions:
            existing = session.scalar(
                select(Indicator).where(
                    Indicator.symbol == definition["symbol"]
                )
            )

            if existing is not None:
                print(
                    f"Indicator already exists: "
                    f"{definition['symbol'].upper()}"
                )
                continue

            indicator = Indicator(
                symbol=definition["symbol"],
                name=definition["name"],
                category=definition["category"],
                frequency=definition["frequency"],
                units=definition["units"],
                source_id=ny_fed.id,
                active=True,
            )

            session.add(indicator)

            print(
                f"Added indicator: "
                f"{definition['symbol'].upper()}"
            )

        session.commit()

        print("\nDatabase seed complete.")


if __name__ == "__main__":
    seed_database()