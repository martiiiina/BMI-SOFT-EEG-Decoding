# ================================================================
# 0. Section: IMPORTS
# ================================================================
import argparse
import numpy as np
import pandas as pd
import pyxdf
from datetime import date
from pathlib import Path


# ================================================================
# 1. Section: INPUTS
# ================================================================
ROOT = Path(__file__).resolve().parents[2]

N_EEG = 64                 # EEG channels are the first 64 columns, the trigger line is the last one
FLAT_UV = 1                # channels with a 1st-99th percentile range below this (uV) are flat
ART_UV = 150               # |amplitude| above this counts as an artifact sample


# ================================================================
# 2. Section: METRICS
# ================================================================
def signal_metrics(X: np.ndarray) -> tuple[dict, np.ndarray]:
    """Per-channel 1st-99th percentile range (uV) plus summary values."""
    X = X - X.mean(0)
    lo, hi = np.percentile(X, [1, 99], axis=0)
    rng = hi - lo
    return {"range_median_uv": np.median(rng), "range_max_uv": rng.max(), "range_min_uv": rng.min(),
            "n_flat": int((rng < FLAT_UV).sum()), "art_frac": (np.abs(X) > ART_UV).mean()}, rng


def marker_metrics(trig: np.ndarray) -> dict:
    """Number of trigger events (rising edges of the trigger line) for each code."""
    c = trig.astype(np.int64)
    codes = c[np.flatnonzero((c[1:] != 0) & (c[:-1] == 0)) + 1]
    values, counts = np.unique(codes, return_counts=True)
    return {"n_events": len(codes), **{f"code_{v}": int(n) for v, n in zip(values, counts)}}


def session_metrics(path: Path) -> tuple[dict, np.ndarray]:
    streams, _ = pyxdf.load_xdf(str(path), dejitter_timestamps=False)
    s = max(streams, key=lambda st: int(st["info"]["channel_count"][0]))      # the EEG stream
    x = np.asarray(s["time_series"], dtype=np.float32)
    fs = float(s["info"]["nominal_srate"][0])

    sig, rng = signal_metrics(x[:, :N_EEG])
    return {"duration_s": len(x) / fs, **sig, **marker_metrics(x[:, -1])}, rng


# ================================================================
# 3. Section: CLI + MAIN
# ================================================================
def _iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid YYYY-MM-DD date")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Protocol quality metrics of the XDF sessions in data/bids/<date>/.")
    p.add_argument("--start", type=_iso_date, metavar="YYYY-MM-DD", help="first session date (inclusive)")
    p.add_argument("--end", type=_iso_date, metavar="YYYY-MM-DD", help="last session date (inclusive)")
    p.add_argument("--data", default=str(ROOT / "data" / "bids"), help="folder with the date folders")
    p.add_argument("--out", default=str(ROOT / "results" / "qc"), help="output folder (CSVs)")
    a = p.parse_args()
    if a.start and a.end and a.start > a.end:
        p.error("--start must not be after --end")
    return a


if __name__ == "__main__":
    args = parse_args()
    data, out = Path(args.data), Path(args.out)

    files = []
    for f in sorted(data.glob("*/**/*.xdf")):
        try:
            day = date.fromisoformat(f.relative_to(data).parts[0])
        except ValueError:
            continue
        in_range = (args.start is None or day >= args.start) and (args.end is None or day <= args.end)
        if in_range and "_old" not in f.name:       # *_old*.xdf are backups of aborted recordings
            files.append(f)
    if not files:
        raise SystemExit(f"No .xdf files found in {data} for the requested dates.")

    rows, ranges = [], {}
    for f in files:
        name = "/".join(f.relative_to(data).parts[:3])      # date/sub/ses (file names can be wrong)
        try:
            row, ranges[name] = session_metrics(f)
            rows.append({"session": name, **row})
            print(f"{name}: {row['duration_s']:.0f} s, {row['n_events']} events, {row['n_flat']} flat channels")
        except Exception as e:                               # one broken file must not stop the batch
            print(f"{name}: could not process ({type(e).__name__}: {e})")

    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).round(3).to_csv(out / "qc_summary.csv", index=False)
    pd.DataFrame(ranges).T.round(1).to_csv(out / "qc_channel_range.csv", index_label="session")
    print(f"Saved qc_summary.csv and qc_channel_range.csv to {out}")
