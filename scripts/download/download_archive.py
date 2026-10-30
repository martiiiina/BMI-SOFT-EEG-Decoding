# ================================================================
# 0. Section: IMPORTS
# ================================================================
import os
import argparse
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from bmieeg.download import Downloader, ArchiveSpecs


# ================================================================
# 1. Section: INPUTS
# ================================================================
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


# ================================================================
# 2. Section: CLI
# ================================================================
def _iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid YYYY-MM-DD date")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download BIDS session data from the EPFL MAKE archive. "
                    "Without --start/--end, every session date is downloaded."
    )
    parser.add_argument("--start", type=_iso_date, metavar="YYYY-MM-DD",
                        help="first session date to download (inclusive)")
    parser.add_argument("--end", type=_iso_date, metavar="YYYY-MM-DD",
                        help="last session date to download (inclusive)")
    parser.add_argument("--dest", default=str(ROOT / "data" / "bids"),
                        help="local destination folder (default: data/bids)")
    parser.add_argument("--dry-run", action="store_true",
                        help="list the files that would be downloaded, without downloading")

    args = parser.parse_args()
    if args.start and args.end and args.start > args.end:
        parser.error("--start must not be after --end")
    return args


# ================================================================
# 3. Section: MAIN
# ================================================================
if __name__ == '__main__':
    args = parse_args()

    specs = ArchiveSpecs(
        dest=args.dest,
        url="EPFL N-pulse/Quality Management System/BMI/bids/",
        username=str(os.getenv("MAKER_USERNAME")),
        password=str(os.getenv("MAKER_APP_PASSWORD")),
        dav_user=str(os.getenv("MAKER_DAV_USER")),
        extra={
            "ignore": ["emg"],
            "date_range": (args.start, args.end),
            "dry_run": args.dry_run,
        }
    )

    downloader = Downloader()
    downloader.run(specs)
