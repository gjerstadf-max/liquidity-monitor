from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import select

from backend.collectors.treasury_fiscaldata import (
    TreasuryAuction,
)
from backend.database.connection import (
    get_session,
)
from backend.database.models import (
    TreasuryAuctionRecord,
)


# =============================================================
# RESULT
# =============================================================


@dataclass(frozen=True)
class AuctionStoreResult:
    received: int
    inserted: int
    updated: int
    skipped: int

    latest_auction_date: date | None


# =============================================================
# FIELDS
# =============================================================


AUCTION_DATA_FIELDS = (
    "record_date",
    "security_type",
    "security_term",
    "announcement_date",
    "issue_date",
    "maturity_date",
    "reopening",
    "cash_management_bill",
    "offering_amount_dollars",
    "competitive_tendered_dollars",
    "competitive_accepted_dollars",
    "noncompetitive_accepted_dollars",
    "fima_tendered_dollars",
    "fima_accepted_dollars",
    "soma_tendered_dollars",
    "soma_accepted_dollars",
    "total_tendered_dollars",
    "total_accepted_dollars",
    "primary_dealer_tendered_dollars",
    "primary_dealer_accepted_dollars",
    "indirect_bidder_tendered_dollars",
    "indirect_bidder_accepted_dollars",
    "direct_bidder_tendered_dollars",
    "direct_bidder_accepted_dollars",
    "treasury_retail_accepted_dollars",
    "bid_to_cover_ratio",
    "high_investment_rate",
    "currently_outstanding_dollars",
    "estimated_public_maturing_dollars",
)


# =============================================================
# CREATE
# =============================================================


def _new_record(
    auction: TreasuryAuction,
) -> TreasuryAuctionRecord:
    """
    Convert a normalized TreasuryAuction into a
    persistent database record.
    """

    return TreasuryAuctionRecord(
        cusip=
            auction.cusip,

        auction_date=
            auction.auction_date,

        **{
            field:
                getattr(
                    auction,
                    field,
                )

            for field
            in AUCTION_DATA_FIELDS
        },
    )


# =============================================================
# UPDATE
# =============================================================

def _update_record(
    record: TreasuryAuctionRecord,
    auction: TreasuryAuction,
) -> bool:
    """
    Apply newly retrieved auction information.

    Existing non-null data are never replaced by a
    newly missing value. This allows auction records
    to become progressively more complete as Treasury
    publishes announcement, result and settlement data.

    Returns True when at least one stored field changes.
    """

    changed = False

    for field in AUCTION_DATA_FIELDS:

        new_value = getattr(
            auction,
            field,
        )

        old_value = getattr(
            record,
            field,
        )

        # Never erase previously known information
        # because a later source response is incomplete.
        if (
            new_value is None
            and old_value is not None
        ):
            continue

        if old_value != new_value:

            setattr(
                record,
                field,
                new_value,
            )

            changed = True

    return changed


# =============================================================
# STORE
# =============================================================


def store_treasury_auctions(
    auctions: list[TreasuryAuction],
) -> AuctionStoreResult:
    """
    Insert or update Treasury auction records.

    Unique identity:

        CUSIP + auction_date

    Announced auctions may initially contain NULL auction
    results. Subsequent refreshes update the same row once
    Treasury publishes the completed results.
    """

    if not auctions:
        return AuctionStoreResult(
            received=0,
            inserted=0,
            updated=0,
            skipped=0,
            latest_auction_date=None,
        )

    inserted = 0
    updated = 0
    skipped = 0

    with get_session() as session:

        for auction in auctions:

            record = session.scalar(
                select(
                    TreasuryAuctionRecord
                )
                .where(
                    TreasuryAuctionRecord.cusip
                    == auction.cusip
                )
                .where(
                    TreasuryAuctionRecord.auction_date
                    == auction.auction_date
                )
            )

            # -------------------------------------------------
            # INSERT
            # -------------------------------------------------

            if record is None:

                session.add(
                    _new_record(
                        auction
                    )
                )

                inserted += 1

                continue

            # -------------------------------------------------
            # UPDATE
            # -------------------------------------------------

            changed = (
                _update_record(
                    record=
                        record,

                    auction=
                        auction,
                )
            )

            if changed:
                updated += 1

            else:
                skipped += 1

        session.commit()

    latest_auction_date = max(
        auction.auction_date
        for auction
        in auctions
    )

    return AuctionStoreResult(
        received=
            len(auctions),

        inserted=
            inserted,

        updated=
            updated,

        skipped=
            skipped,

        latest_auction_date=
            latest_auction_date,
    )