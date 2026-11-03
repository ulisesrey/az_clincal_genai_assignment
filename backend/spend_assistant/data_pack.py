import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

INVOICES_FILE = "invoices_2025_clean.csv"
VENDOR_MASTER_FILE = "vendor_master.csv"
POLICY_FILE = "procurement_policy.md"
EXPECTED_FILES = (INVOICES_FILE, VENDOR_MASTER_FILE, POLICY_FILE)

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class DataPackMissingError(Exception):
    def __init__(self, data_dir: Path, missing: list[str]):
        self.data_dir = data_dir
        self.missing = missing
        super().__init__(
            f"Data pack incomplete in {data_dir}. Missing: {', '.join(missing)}. "
            "Place the supplied files there or set DATA_DIR to their location."
        )


@dataclass(frozen=True)
class DataPack:
    invoices: pd.DataFrame
    vendors: pd.DataFrame
    policy_text: str


def resolve_data_dir() -> Path:
    return Path(os.environ.get("DATA_DIR", DEFAULT_DATA_DIR)).resolve()


def load_data_pack(data_dir: Path) -> DataPack:
    missing = [name for name in EXPECTED_FILES if not (data_dir / name).is_file()]
    if missing:
        raise DataPackMissingError(data_dir, missing)

    invoices = pd.read_csv(
        data_dir / INVOICES_FILE,
        dtype={"amount": str, "po_number": "string", "approved_by": "string"},
        parse_dates=["invoice_date"],
    )
    vendors = pd.read_csv(data_dir / VENDOR_MASTER_FILE)
    policy_text = (data_dir / POLICY_FILE).read_text(encoding="utf-8")
    return DataPack(invoices=invoices, vendors=vendors, policy_text=policy_text)
