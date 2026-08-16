"""Download the Online Retail dataset."""

from __future__ import annotations

import kagglehub

from src.config import Config, cfg


def download_dataset(config: Config | None = None) -> str:
    """Download the configured dataset into the raw data directory."""
    active_config = config or cfg()
    return kagglehub.dataset_download(
        active_config.dataset.slug,
        output_dir=active_config.paths.raw_dir,
    )


def run_fetch() -> None:
    download_dataset()


if __name__ == "__main__":
    run_fetch()
