from __future__ import annotations

from dataclasses import dataclass

from datetime import date

from decimal import Decimal

import httpx


# =============================================================
# SOURCE
# =============================================================


TREASURY_AUCTIONS_API_URL = (
    "https://api.fiscaldata.treasury.gov/"
    "services/api/fiscal_service/v1/"
    "accounting/od/auctions_query"
)


# =============================================================
# DATA OBJECT
# =============================================================


@dataclass(frozen=True)
class TreasuryAuction:
    """
    One Treasury auction record from Treasury FiscalData.

    Dollar amounts are retained in source dollars.

    Auction records may exist before the auction occurs.
    In that case, supply information such as offering amount
    may be populated while auction-result fields remain None.
    """

    record_date: date

    cusip: str

    security_type: str
    security_term: str

    announcement_date: date | None
    auction_date: date
    issue_date: date
    maturity_date: date

    reopening: bool | None
    cash_management_bill: bool | None

    offering_amount_dollars: Decimal | None

    competitive_tendered_dollars: Decimal | None
    competitive_accepted_dollars: Decimal | None

    noncompetitive_accepted_dollars: Decimal | None

    fima_tendered_dollars: Decimal | None
    fima_accepted_dollars: Decimal | None

    soma_tendered_dollars: Decimal | None
    soma_accepted_dollars: Decimal | None

    total_tendered_dollars: Decimal | None
    total_accepted_dollars: Decimal | None

    primary_dealer_tendered_dollars: Decimal | None
    primary_dealer_accepted_dollars: Decimal | None

    indirect_bidder_tendered_dollars: Decimal | None
    indirect_bidder_accepted_dollars: Decimal | None

    direct_bidder_tendered_dollars: Decimal | None
    direct_bidder_accepted_dollars: Decimal | None

    treasury_retail_accepted_dollars: Decimal | None

    bid_to_cover_ratio: Decimal | None

    high_investment_rate: Decimal | None

    currently_outstanding_dollars: Decimal | None

    estimated_public_maturing_dollars: Decimal | None

    # ---------------------------------------------------------
    # STATUS
    # ---------------------------------------------------------

    @property
    def is_completed(self) -> bool:
        """
        True when actual auction-result data are available.
        """

        return (
            self.bid_to_cover_ratio
            is not None
            and self.competitive_accepted_dollars
            is not None
        )

    # ---------------------------------------------------------
    # COMPETITIVE BIDDER TOTAL
    # ---------------------------------------------------------

    @property
    def competitive_bidder_accepted_total(
        self,
    ) -> Decimal | None:
        """
        Primary dealer + indirect + direct awards.

        These should reconcile to competitive accepted.
        """

        values = (
            self.primary_dealer_accepted_dollars,
            self.indirect_bidder_accepted_dollars,
            self.direct_bidder_accepted_dollars,
        )

        if any(
            value is None
            for value in values
        ):
            return None

        return sum(
            (
                value
                for value in values
                if value is not None
            ),
            Decimal("0"),
        )

    @property
    def competitive_bidder_reconciles(
        self,
    ) -> bool | None:
        """
        Confirm bidder awards reconcile to
        competitive accepted.
        """

        bidder_total = (
            self.competitive_bidder_accepted_total
        )

        if (
            bidder_total is None
            or self.competitive_accepted_dollars
            is None
        ):
            return None

        return (
            bidder_total
            == self.competitive_accepted_dollars
        )

    # ---------------------------------------------------------
    # PUBLIC AUCTION TOTALS
    # ---------------------------------------------------------

    @property
    def public_accepted_dollars(
        self,
    ) -> Decimal | None:
        """
        Competitive + noncompetitive + FIMA awards.

        SOMA awards are excluded.
        """

        values = (
            self.competitive_accepted_dollars,
            self.noncompetitive_accepted_dollars,
            self.fima_accepted_dollars,
        )

        if any(
            value is None
            for value in values
        ):
            return None

        return sum(
            (
                value
                for value in values
                if value is not None
            ),
            Decimal("0"),
        )

    # ---------------------------------------------------------
    # BIDDER SHARES
    # ---------------------------------------------------------

    def _competitive_share(
        self,
        accepted: Decimal | None,
    ) -> Decimal | None:

        denominator = (
            self.competitive_accepted_dollars
        )

        if (
            accepted is None
            or denominator is None
            or denominator == 0
        ):
            return None

        return (
            accepted
            / denominator
        )

    @property
    def primary_dealer_share(
        self,
    ) -> Decimal | None:
        return self._competitive_share(
            self.primary_dealer_accepted_dollars
        )

    @property
    def indirect_bidder_share(
        self,
    ) -> Decimal | None:
        return self._competitive_share(
            self.indirect_bidder_accepted_dollars
        )

    @property
    def direct_bidder_share(
        self,
    ) -> Decimal | None:
        return self._competitive_share(
            self.direct_bidder_accepted_dollars
        )


# =============================================================
# PARSING
# =============================================================


def _parse_decimal(
    value,
) -> Decimal | None:

    if value in (
        None,
        "",
        "null",
    ):
        return None

    return Decimal(
        str(value)
    )


def _parse_date(
    value,
) -> date | None:

    if value in (
        None,
        "",
        "null",
    ):
        return None

    return date.fromisoformat(
        str(value)
    )


def _parse_yes_no(
    value,
) -> bool | None:

    if value is None:
        return None

    normalized = (
        str(value)
        .strip()
        .lower()
    )

    if normalized == "yes":
        return True

    if normalized == "no":
        return False

    return None


def _parse_auction(
    row: dict,
) -> TreasuryAuction:
    """
    Convert one FiscalData row into a normalized
    TreasuryAuction object.

    Missing auction-result fields remain None.
    """

    record_date = _parse_date(
        row.get(
            "record_date"
        )
    )

    auction_date = _parse_date(
        row.get(
            "auction_date"
        )
    )

    issue_date = _parse_date(
        row.get(
            "issue_date"
        )
    )

    maturity_date = _parse_date(
        row.get(
            "maturity_date"
        )
    )

    if record_date is None:
        raise ValueError(
            "Treasury auction record_date "
            "is missing."
        )

    if auction_date is None:
        raise ValueError(
            "Treasury auction auction_date "
            "is missing."
        )

    if issue_date is None:
        raise ValueError(
            "Treasury auction issue_date "
            "is missing."
        )

    if maturity_date is None:
        raise ValueError(
            "Treasury auction maturity_date "
            "is missing."
        )

    return TreasuryAuction(
        record_date=
            record_date,

        cusip=
            str(
                row.get(
                    "cusip",
                    "",
                )
            ),

        security_type=
            str(
                row.get(
                    "security_type",
                    "",
                )
            ),

        security_term=
            str(
                row.get(
                    "security_term",
                    "",
                )
            ),

        announcement_date=
            _parse_date(
                row.get(
                    "announcemt_date"
                )
            ),

        auction_date=
            auction_date,

        issue_date=
            issue_date,

        maturity_date=
            maturity_date,

        reopening=
            _parse_yes_no(
                row.get(
                    "reopening"
                )
            ),

        cash_management_bill=
            _parse_yes_no(
                row.get(
                    "cash_management_bill_cmb"
                )
            ),

        offering_amount_dollars=
            _parse_decimal(
                row.get(
                    "offering_amt"
                )
            ),

        competitive_tendered_dollars=
            _parse_decimal(
                row.get(
                    "comp_tendered"
                )
            ),

        competitive_accepted_dollars=
            _parse_decimal(
                row.get(
                    "comp_accepted"
                )
            ),

        noncompetitive_accepted_dollars=
            _parse_decimal(
                row.get(
                    "noncomp_accepted"
                )
            ),

        fima_tendered_dollars=
            _parse_decimal(
                row.get(
                    "fima_noncomp_tendered"
                )
            ),

        fima_accepted_dollars=
            _parse_decimal(
                row.get(
                    "fima_noncomp_accepted"
                )
            ),

        soma_tendered_dollars=
            _parse_decimal(
                row.get(
                    "soma_tendered"
                )
            ),

        soma_accepted_dollars=
            _parse_decimal(
                row.get(
                    "soma_accepted"
                )
            ),

        total_tendered_dollars=
            _parse_decimal(
                row.get(
                    "total_tendered"
                )
            ),

        total_accepted_dollars=
            _parse_decimal(
                row.get(
                    "total_accepted"
                )
            ),

        primary_dealer_tendered_dollars=
            _parse_decimal(
                row.get(
                    "primary_dealer_tendered"
                )
            ),

        primary_dealer_accepted_dollars=
            _parse_decimal(
                row.get(
                    "primary_dealer_accepted"
                )
            ),

        indirect_bidder_tendered_dollars=
            _parse_decimal(
                row.get(
                    "indirect_bidder_tendered"
                )
            ),

        indirect_bidder_accepted_dollars=
            _parse_decimal(
                row.get(
                    "indirect_bidder_accepted"
                )
            ),

        direct_bidder_tendered_dollars=
            _parse_decimal(
                row.get(
                    "direct_bidder_tendered"
                )
            ),

        direct_bidder_accepted_dollars=
            _parse_decimal(
                row.get(
                    "direct_bidder_accepted"
                )
            ),

        treasury_retail_accepted_dollars=
            _parse_decimal(
                row.get(
                    "treas_retail_accepted"
                )
            ),

        bid_to_cover_ratio=
            _parse_decimal(
                row.get(
                    "bid_to_cover_ratio"
                )
            ),

        high_investment_rate=
            _parse_decimal(
                row.get(
                    "high_investment_rate"
                )
            ),

        currently_outstanding_dollars=
            _parse_decimal(
                row.get(
                    "currently_outstanding"
                )
            ),

        estimated_public_maturing_dollars=
            _parse_decimal(
                row.get(
                    "est_pub_held_mat_by_type_amt"
                )
            ),
    )


# =============================================================
# FETCH
# =============================================================


def fetch_treasury_bill_auctions(
    count: int = 100,
    completed_only: bool = False,
) -> list[TreasuryAuction]:
    """
    Fetch the latest Treasury bill auction records.

    Treasury publishes auction records when announced,
    so future auctions may be returned with result fields
    still missing.

    completed_only=True removes announced auctions whose
    auction results have not yet been published.
    """

    if count < 1:
        raise ValueError(
            "count must be at least 1"
        )

    response = httpx.get(
        TREASURY_AUCTIONS_API_URL,
        params={
            "filter":
                "security_type:eq:Bill",

            "sort":
                "-auction_date",

            "page[size]":
                count,
        },
        timeout=30.0,
    )

    response.raise_for_status()

    payload = (
        response.json()
    )

    rows = (
        payload.get(
            "data",
            []
        )
    )

    auctions = [
        _parse_auction(
            row
        )

        for row
        in rows
    ]

    if completed_only:
        auctions = [
            auction

            for auction
            in auctions

            if auction.is_completed
        ]

    return auctions


# =============================================================
# TERMINAL TEST
# =============================================================


def print_latest_completed_bill_auctions(
    count: int = 10,
) -> None:

    auctions = (
        fetch_treasury_bill_auctions(
            count=100,
            completed_only=True,
        )
    )

    for auction in auctions[:count]:

        print()
        print(
            "=" * 72
        )

        print(
            f"{auction.auction_date}  "
            f"{auction.security_term}"
        )

        print(
            f"Offering: "
            f"${auction.offering_amount_dollars:,.0f}"
        )

        print(
            f"Bid-to-cover: "
            f"{auction.bid_to_cover_ratio}"
        )

        print(
            f"Primary dealer share: "
            f"{float(auction.primary_dealer_share) * 100:.1f}%"
        )

        print(
            f"Indirect share: "
            f"{float(auction.indirect_bidder_share) * 100:.1f}%"
        )

        print(
            f"Direct share: "
            f"{float(auction.direct_bidder_share) * 100:.1f}%"
        )

        print(
            "Competitive reconciliation:",
            auction.competitive_bidder_reconciles,
        )


if __name__ == "__main__":
    print_latest_completed_bill_auctions()