import bisect
import csv
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

REPORTING_CURRENCY = "EUR"
CENT = Decimal("0.01")
SNAPSHOT_PATH = Path(__file__).parent / "resources" / "ecb_reference_rates_2025.csv"


@dataclass(frozen=True)
class Conversion:
    eur_equivalent: Decimal
    ecb_rate: Decimal | None
    rate_date: date | None


class EcbRates:
    """Frozen ECB reference rates (units of currency per 1 EUR), see ADR 0002."""

    def __init__(self, snapshot_path: Path = SNAPSHOT_PATH):
        with snapshot_path.open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self._currencies = [name for name in rows[0] if name != "rate_date"]
        self._dates = [date.fromisoformat(row["rate_date"]) for row in rows]
        self._rates = [{ccy: Decimal(row[ccy]) for ccy in self._currencies} for row in rows]

    def to_eur(self, amount: Decimal, currency: str, on: date) -> Conversion:
        if currency == REPORTING_CURRENCY:
            return Conversion(amount.quantize(CENT, ROUND_HALF_UP), None, None)
        if currency not in self._currencies:
            raise ValueError(f"No ECB reference rate for currency {currency}")
        # Most recent ECB publication on or before the date covers weekends and holidays.
        index = bisect.bisect_right(self._dates, on) - 1
        if index < 0:
            raise ValueError(f"No ECB reference rate on or before {on}")
        rate = self._rates[index][currency]
        return Conversion((amount / rate).quantize(CENT, ROUND_HALF_UP), rate, self._dates[index])
