"""Clean the Online Retail dataset and produce a quality report."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.config import Config, cfg


class CleanReport:
    """Track row-count changes across cleaning steps."""

    def __init__(self, dataframe: pd.DataFrame) -> None:
        self.dataframe = dataframe
        self.raw_len = len(dataframe)
        self.curr_len = self.raw_len
        self.records: list[tuple[str, int, int]] = []

    def add_record(self, name: str) -> None:
        before = self.curr_len
        after = len(self.dataframe)
        self.curr_len = after
        self.records.append((name, before, after))

    def save(self, path: str | Path) -> None:
        record_df = pd.DataFrame(
            self.records,
            columns=["步骤名", "处理前", "处理后"],
        )
        record_df["删除量"] = record_df["处理前"] - record_df["处理后"]
        record_df["变化率"] = round(record_df["处理后"] / record_df["处理前"], 4)
        record_df["总变化率"] = round(record_df["处理后"] / self.raw_len, 4)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        record_df.to_csv(path, index=False)


def load_raw_data(config: Config) -> pd.DataFrame:
    """Load the raw CSV file using dataset encoding."""
    return pd.read_csv(
        Path(config.paths.raw_dir, config.files.raw),
        encoding=config.dataset.encoding,
    )


def clean_data(
    dataframe: pd.DataFrame,
    report: CleanReport,
    config: Config,
) -> pd.DataFrame:
    """Apply configured cleaning rules and record each step."""
    dataframe["InvoiceDate"] = pd.to_datetime(
        dataframe["InvoiceDate"].str.strip(),
        format=config.dataset.date_format,
    ).dt.date
    report.add_record("Parse Datetime")

    dataframe["StockCode"] = dataframe["StockCode"].str.strip().str.upper()
    dataframe["Description"] = dataframe["Description"].str.strip().str.title()
    dataframe["Country"] = dataframe["Country"].str.strip().str.title()
    report.add_record("Format Texts")

    dataframe.loc[dataframe["InvoiceNo"].str.match("^[AC]"), "InvoiceNo"] = np.nan
    dataframe.dropna(subset=["InvoiceNo"], inplace=True)
    report.add_record("Drop A/C Invoice")

    dataframe.dropna(subset=["CustomerID"], inplace=True)
    report.add_record("Drop Null CustomerID")

    dataframe.loc[dataframe["Quantity"] <= 0, "Quantity"] = pd.NA
    dataframe.dropna(subset=["Quantity"], inplace=True)
    report.add_record("Drop Negative Quantity")

    dataframe.loc[dataframe["UnitPrice"] <= 0, "UnitPrice"] = pd.NA
    dataframe.dropna(subset=["UnitPrice"], inplace=True)
    report.add_record("Drop Negative Unit Price")

    dataframe.loc[
        ~dataframe["StockCode"].str.match(config.cleaning.valid_stock_code_pattern),
        "StockCode",
    ] = pd.NA
    dataframe.dropna(subset=["StockCode"], inplace=True)
    report.add_record("Drop Error Stock Code")

    if config.cleaning.drop_duplicates:
        dataframe.drop_duplicates(inplace=True)
    report.add_record("Drop Duplicates")

    dataframe["InvoiceNo"] = dataframe["InvoiceNo"].astype("int32")
    dataframe.set_index(config.dataset.index_columns, inplace=True)
    dataframe["LineAmount"] = round(dataframe["Quantity"] * dataframe["UnitPrice"], 2)
    return dataframe


def save_cleaned_data(
    dataframe: pd.DataFrame,
    report: CleanReport,
    config: Config,
) -> None:
    """Write cleaned Parquet data and the quality report."""
    interim_dir = Path(config.paths.interim_dir)
    interim_dir.mkdir(parents=True, exist_ok=True)
    dataframe.to_parquet(Path(interim_dir, config.files.cleaned))
    report.save(Path(interim_dir, config.files.quality_report))


def run_clean() -> None:
    config = cfg()
    raw_data = load_raw_data(config)
    report = CleanReport(raw_data)
    cleaned_data = clean_data(raw_data, report, config)
    save_cleaned_data(cleaned_data, report, config)
    print(cleaned_data.sample(n=10))


if __name__ == "__main__":
    run_clean()
