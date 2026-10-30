# Download

Ported from the EMG repo (`src/bmiemg/download`).

Layers: `service` (`Downloader`) → `domain` (specs, strategies, registry) → `adapters` (one per source). To add a source, subclass `DownloadStrategy` + `DownloadSpec` under `adapters/` and decorate the strategy with `@Registry.register("<source-name>")`.

## Archive source

Pulls files from EPFL's WebDAV archive (`make-archives.epfl.ch`).

Sessions are uploaded there in BIDS format after acquisition. One `.xdf` holds both
EEG and EMG (64-channel ANT Neuro EEG plus EMG on the AUX channels), split into
`eeg/` and `emg/` folders by the BIDS conversion. This repo reads the same archive
root as the EMG repo and skips the `emg/` folders, via `extra={"ignore": ["emg"]}`
in `scripts/download/download_archive.py`.

1. Requires Python **3.12 or newer** (`domain/download_strategy.py` uses PEP 695
   generic syntax) and [Poetry](https://python-poetry.org/). From the project root,
   install the dependencies and the `bmieeg` package:

   ```bash
   poetry install
   ```

2. Copy `.env.example` to `.env` and fill in your credentials (never commit them).
   Write the values as they are, without the `<>` and without quotes:

   ```env
   MAKER_USERNAME=your_username
   MAKER_APP_PASSWORD=your_app_password
   MAKER_DAV_USER=your_dav_user
   ```

3. Run the download script from the project root (it loads `.env` automatically):

   ```bash
   poetry run python -m scripts.download.download_archive [options]
   ```

   | Option | Meaning |
   |--------|---------|
   | `--start YYYY-MM-DD` | First session date to download (inclusive). |
   | `--end YYYY-MM-DD` | Last session date to download (inclusive). |
   | `--dest PATH` | Local destination folder (default: `data/bids`). |
   | `--dry-run` | List the files that would be downloaded, without downloading. |

   Sessions are stored in one folder per acquisition date (`bids/YYYY-MM-DD/sub-*/ses-*/`),
   and `--start`/`--end` filter on that date. Either bound can be left out. With no
   options, **every** date is downloaded, which is several GB.

   ```bash
   # list what is available in a period (nothing is downloaded)
   poetry run python -m scripts.download.download_archive --start 2026-10-01 --end 2026-10-31 --dry-run

   # download a period
   poetry run python -m scripts.download.download_archive --start 2026-10-01 --end 2026-10-31

   # download a single day
   poetry run python -m scripts.download.download_archive --start 2026-10-07 --end 2026-10-07

   # download everything from a date onwards
   poetry run python -m scripts.download.download_archive --start 2026-09-01

   # everything
   poetry run python -m scripts.download.download_archive
   ```

   Run it from the project root, as a module (`-m`), so that the `scripts` package
   resolves. Files that already exist locally are downloaded again, so use a date
   range instead of re-running the full download.

   Without Poetry, activate your own environment with the dependencies from
   `pyproject.toml` and run `PYTHONPATH=src python -m scripts.download.download_archive`.

   Other options, such as the remote `url` or the folders to ignore (`extra={"ignore": [...]}`),
   are set in `scripts/download/download_archive.py`. Entries at the archive root that are
   not date folders (e.g. `.DS_Store`) are skipped when a date range is given.

### Getting the credentials

- **`MAKER_USERNAME`** — Is your EPFL username
- **`MAKER_APP_PASSWORD`** — Go to Profile Settings (top right) on the Archive MAKE Drive > Security > Create New App Password
- **`MAKER_DAV_USER`** — Go to Files Settings (bottom left) on the Archive MAKE drive > WebDAV > Copy the URL and past the code in the URL that comes after https://make-archives.epfl.ch/remote.php/dav/files/
