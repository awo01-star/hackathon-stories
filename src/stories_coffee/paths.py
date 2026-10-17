"""Default project paths, independent of the shell's working directory."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = PROJECT_ROOT / "data" / "stories_transactions.csv"
DEFAULT_REPORTS = PROJECT_ROOT / "artifacts" / "week_ahead_forecasting"
REFERENCE_REPORTS = PROJECT_ROOT / "artifacts" / "week_ahead_reference"
