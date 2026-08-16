"""Orchestrate the end-to-end RFM analysis pipeline."""

from __future__ import annotations

from src.fetch import run_fetch
from src.clean import run_clean
from src.analyze import run_analyze
from src.report import run_report


def main() -> None:
    print("[1/4] Downloading raw dataset")
    run_fetch()

    print("[2/4] Cleaning raw dataset")
    run_clean()

    print("[3/4] Calculating RFM and customer segments")
    run_analyze()

    print("[4/4] Generating RFM report")
    run_report()

    print("Pipeline completed.")


if __name__ == "__main__":
    main()
