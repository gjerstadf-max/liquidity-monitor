from __future__ import annotations

from decimal import Decimal

from backend.metrics.funding import (
    funding_spread_statistics,
    latest_funding_snapshot,
)
from backend.metrics.repo_market import (
    repo_market_statistics,
)
from backend.metrics.system_liquidity import (
    system_liquidity_history_metrics,
    system_liquidity_metrics,
)
from backend.metrics.treasury_intermediation import (
    treasury_intermediation_statistics,
)


# =============================================================
# FORMATTING
# =============================================================


def _format_billions(
    value: Decimal | float,
    decimals: int = 0,
) -> str:
    numeric = float(
        value
    )

    if numeric < 0:
        return (
            f"-${abs(numeric):,.{decimals}f}B"
        )

    return (
        f"${numeric:,.{decimals}f}B"
    )


def _format_bp(
    value: Decimal | float,
    decimals: int = 0,
) -> str:
    return (
        f"{float(value):+,.{decimals}f} bp"
    )


def _format_sigma(
    value: float,
) -> str:
    return (
        f"{value:+.2f}σ"
    )


# =============================================================
# FUNDING
# =============================================================


def funding_what_matters() -> str:
    return (
        "Funding Conditions measures relative pressure in "
        "overnight secured funding, principally through the "
        "relationship between SOFR and unsecured reference "
        "rates such as EFFR. Persistent positive widening can "
        "signal greater secured-funding pressure, while large "
        "negative divergence is treated as unusual but not as "
        "equivalent evidence of funding stress."
    )



def funding_watch(
    verdict: str,
) -> str:
    if verdict == "Normal":
        return (
            "Funding: overnight secured and unsecured rates "
            "remain well aligned. Watch for a persistent "
            "widening in SOFR relative to EFFR or other "
            "unsecured reference rates."
        )

    if verdict == "Watch":
        return (
            "Funding: conditions are less comfortable than "
            "normal. Watch whether recent spread pressure "
            "persists or begins appearing across multiple "
            "overnight funding benchmarks."
        )

    if verdict == "Elevated":
        return (
            "Funding: pricing pressure is materially elevated. "
            "Watch for persistence, broader secured/unsecured "
            "divergence, and evidence that funding pressure is "
            "spreading across venues."
        )

    return (
        "Funding: conditions are stressed. Watch the scale "
        "and persistence of rate dislocations and any signs "
        "that funding availability is becoming impaired."
    )


# =============================================================
# SYSTEM LIQUIDITY
# =============================================================


def system_liquidity_what_matters() -> str:
    return (
        "System Liquidity tracks reserve balances plus ON RRP "
        "less the Treasury General Account as a monitoring proxy "
        "for the liquidity buffer available to absorb funding "
        "and Treasury cash-flow demands. Both the level and its "
        "four- and thirteen-week direction are evaluated. The "
        "proxy is not a measure of total financial-system liquidity."
    )


def system_liquidity_watch(
    verdict: str,
) -> str:
    if verdict == "Normal":
        return (
            "System liquidity remains broadly comfortable. "
            "Watch for sustained declines in reserve balances, "
            "continued depletion of ON RRP, or TGA accumulation "
            "that materially reduces the liquidity buffer."
        )

    if verdict == "Watch":
        return (
            "System liquidity is becoming less comfortable. "
            "Watch whether reserve balances continue to decline, "
            "ON RRP remains largely exhausted, or TGA accumulation "
            "removes additional liquidity from the banking system."
        )

    if verdict == "Elevated":
        return (
            "System liquidity is under meaningful pressure. "
            "Watch the pace of reserve decline and whether "
            "Treasury cash accumulation continues to drain "
            "available liquidity."
        )

    return (
        "The available system-liquidity buffer is materially "
        "stressed. Reserve balances, Treasury cash flows and "
        "remaining ON RRP capacity require close monitoring."
    )

# =============================================================
# REPO MARKET
# =============================================================


def repo_what_matters() -> str:
    return (
        "Repo Market Pressure measures whether secured overnight "
        "funding is becoming broadly dislocated. It evaluates "
        "differences among SOFR, TGCR and BGCR together with "
        "SOFR transaction dispersion and upper-tail pricing, "
        "allowing isolated rate moves to be distinguished from "
        "broader repo-market pressure."
    )

def repo_watch(
    verdict: str,
) -> str:
    if verdict == "Normal":
        return (
            "Repo market: secured funding remains orderly. "
            "Watch for widening differences between SOFR, "
            "TGCR and BGCR, or a sharp increase in SOFR "
            "dispersion and upper-tail pricing."
        )

    if verdict == "Watch":
        return (
            "Repo market: one or more repo diagnostics are "
            "unusually elevated, but evidence of broader "
            "dysfunction remains limited. Watch for "
            "confirmation across multiple repo measures."
        )

    if verdict == "Elevated":
        return (
            "Repo market: pressure is elevated across multiple "
            "secured-funding diagnostics. Watch whether "
            "dispersion, venue differences and upper-tail "
            "pricing continue to worsen."
        )

    return (
        "Repo market: secured funding is showing broad "
        "dysfunction. Watch the persistence of pricing "
        "dislocations and whether pressure spreads further "
        "across Treasury financing channels."
    )


# =============================================================
# TREASURY INTERMEDIATION
# =============================================================


def treasury_intermediation_what_matters() -> str:
    return (
        "Treasury Intermediation evaluates whether dealer "
        "balance-sheet adjustment, Treasury trading and borrowing "
        "demand, and settlement friction are becoming unusually "
        "strained. The factor looks for convergence across these "
        "dimensions rather than treating a single unusual measure "
        "as evidence of broad Treasury-market dysfunction."
    )


def treasury_intermediation_watch(
    verdict: str,
) -> str:
    if verdict == "Normal":
        return (
            "Treasury intermediation: dealer balance-sheet "
            "adjustment, intermediation demand and settlement "
            "friction remain orderly. Watch for unusual "
            "movement across more than one of these dimensions "
            "at the same time."
        )

    if verdict == "Watch":
        return (
            "Treasury intermediation: one dimension is "
            "unusually elevated, but the other dealer-market "
            "indicators do not confirm broad pressure. Watch "
            "for convergence across balance-sheet adjustment, "
            "trading/borrowing demand and settlement fails."
        )

    if verdict == "Elevated":
        return (
            "Treasury intermediation: pressure is evident "
            "across multiple dealer-market dimensions. Watch "
            "whether settlement friction intensifies and "
            "whether abnormal dealer balance-sheet adjustment "
            "and intermediation demand persist together."
        )

    return (
        "Treasury intermediation: dealer balance-sheet "
        "adjustment, intermediation demand and settlement "
        "friction are showing broad stress. Watch whether "
        "market functioning begins to normalize or whether "
        "the disruption persists across multiple weeks."
    )
# =============================================================
# TREASURY MARKET ACTIVITY
# =============================================================


def treasury_market_activity_what_matters() -> str:
    """
    Explain the economic purpose of Factor #5.
    """

    return (
        "Treasury Market Activity measures whether the "
        "market is being asked to absorb an unusually "
        "large volume of Treasury bill issuance and "
        "whether auction results indicate difficulty "
        "absorbing that supply. Gross bill issuance and "
        "auction absorption are evaluated separately so "
        "that heavy but orderly issuance is distinguished "
        "from genuine market pressure."
    )


def treasury_market_activity_watch(
    verdict: str,
) -> str:
    """
    Describe what should be monitored next for
    Treasury Market Activity.
    """

    if verdict == "Stressed":

        return (
            "Watch for continued weak bid-to-cover ratios, "
            "elevated primary-dealer take-down, persistent "
            "heavy Treasury issuance, repo-market pressure, "
            "and any use of the Standing Repo Facility."
        )

    if verdict == "Elevated":

        return (
            "Watch whether weak auction absorption persists "
            "across multiple bill tenors, whether primary "
            "dealers are required to absorb a larger share "
            "of issuance, and whether repo conditions begin "
            "to confirm Treasury-market pressure."
        )

    if verdict == "Watch":

        return (
            "Watch whether unusually heavy Treasury bill "
            "issuance continues to be absorbed normally. "
            "Particular attention should be paid to "
            "bid-to-cover ratios and primary-dealer "
            "take-down across upcoming auctions."
        )

    return (
        "Watch for a meaningful increase in Treasury bill "
        "supply, deterioration in auction demand, or a "
        "rise in primary-dealer take-down."
    )
def commercial_paper_what_matters() -> str:
    return (
        "Commercial-paper funding conditions provide a direct view "
        "into unsecured short-term corporate financing. The primary "
        "diagnostic is the premium paid by lower-quality A2/P2 "
        "nonfinancial issuers relative to AA nonfinancial issuers."
    )


def commercial_paper_watch(
    verdict: str,
) -> str:

    if verdict == "Normal":
        return (
            "Commercial-paper funding remains orderly, with the "
            "lower-quality funding premium well below levels "
            "historically associated with meaningful market stress."
        )

    if verdict == "Watch":
        return (
            "Commercial-paper funding conditions warrant monitoring "
            "as the lower-quality funding premium has become elevated."
        )

    if verdict == "Elevated":
        return (
            "Commercial-paper funding pressure is elevated, indicating "
            "meaningful deterioration in unsecured short-term "
            "corporate financing conditions."
        )

    return (
        "Commercial-paper funding is severely stressed, with the "
        "lower-quality funding premium at levels historically "
        "associated with major funding-market disruption."
    )
def bank_funding_what_matters() -> str:
    return (
        "Bank funding conditions show whether banks are relying "
        "more heavily on Federal Reserve liquidity or experiencing "
        "unusual deposit pressure. Primary credit is the core "
        "stress measure, while deposit migration and funding "
        "substitution provide confirmation."
    )


def bank_funding_watch(
    verdict: str,
) -> str:

    if verdict == "Normal":
        return (
            "Bank funding conditions remain orderly, with limited "
            "reliance on Federal Reserve primary credit and no "
            "significant deposit-flight signal."
        )

    if verdict == "Watch":
        return (
            "Bank funding conditions warrant monitoring as either "
            "central-bank borrowing or deposit behavior shows "
            "early signs of pressure."
        )

    if verdict == "Elevated":
        return (
            "Bank funding pressure is elevated, with meaningful "
            "liquidity demand or deposit stress indicating tighter "
            "bank funding conditions."
        )

    return (
        "Bank funding is severely stressed, with unusually heavy "
        "reliance on Federal Reserve liquidity indicating acute "
        "banking-system funding pressure."
    )

def global_dollar_funding_what_matters() -> str:
    return (
        "Global dollar funding conditions show whether foreign "
        "institutions are making unusual use of Federal Reserve "
        "dollar-liquidity backstops. Central-bank swap usage is "
        "the core systemic measure, while FIMA repo provides "
        "supporting evidence of foreign-official liquidity demand."
    )


def global_dollar_funding_watch(
    verdict: str,
) -> str:

    if verdict == "Normal":
        return (
            "Global dollar funding remains orderly, with minimal "
            "use of Federal Reserve dollar-liquidity backstops."
        )

    if verdict == "Watch":
        return (
            "Global dollar funding conditions warrant monitoring "
            "as Federal Reserve liquidity facilities show unusual "
            "but still contained demand."
        )

    if verdict == "Elevated":
        return (
            "Global dollar funding pressure is elevated, with "
            "meaningful central-bank swap usage indicating tighter "
            "offshore dollar-funding conditions."
        )

    return (
        "Global dollar funding is severely stressed, with very "
        "large central-bank swap usage indicating acute offshore "
        "dollar-liquidity demand."
    )
