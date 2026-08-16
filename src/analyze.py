"""Compute RFM metrics, segment customers, and save processed outputs."""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from src.config import Config, cfg


CUSTOMER_TYPES = {
    0b111: "重要价值用户",
    0b101: "重要发展用户",
    0b011: "重要保持用户",
    0b001: "重要挽留用户",
    0b110: "一般价值用户",
    0b100: "一般发展用户",
    0b010: "一般保持用户",
    0b000: "一般挽留用户",
}


def create_connection() -> duckdb.DuckDBPyConnection:
    """Create an in-memory DuckDB connection."""
    return duckdb.connect()


def register_cleaned_view(
    connection: duckdb.DuckDBPyConnection,
    input_path: Path,
) -> None:
    """Expose the cleaned Parquet file as ``cleaned_online_retail``."""
    connection.execute(
        f"""
        CREATE OR REPLACE VIEW cleaned_online_retail AS
        SELECT * FROM read_parquet('{input_path.as_posix()}')
        """
    )


def compute_rfm(
    connection: duckdb.DuckDBPyConnection,
    config: Config,
) -> pd.DataFrame:
    """Run the RFM SQL query and return the resulting DataFrame."""
    return connection.execute(
        """
        WITH rfm AS (
            SELECT
                CustomerID AS customer_id,
                DATEDIFF(
                    'day',
                    MAX(InvoiceDate),
                    CAST(? AS DATE)
                ) AS recency_days,
                COUNT(DISTINCT InvoiceNo) AS frequency,
                ROUND(SUM(LineAmount), 2) AS monetary
            FROM cleaned_online_retail
            GROUP BY CustomerID
        )
        SELECT
            customer_id,
            recency_days,
            frequency,
            monetary,
            NTILE(?) OVER (ORDER BY recency_days DESC) AS r_score,
            NTILE(?) OVER (ORDER BY frequency ASC) AS f_score,
            NTILE(?) OVER (ORDER BY monetary ASC) AS m_score,
            PERCENT_RANK() OVER (ORDER BY recency_days ASC) AS r_rank,
            PERCENT_RANK() OVER (ORDER BY frequency DESC) AS f_rank,
            PERCENT_RANK() OVER (ORDER BY monetary DESC) AS m_rank
        FROM rfm
        ORDER BY r_rank ASC, f_rank ASC, m_rank ASC
        """,
        [
            config.rfm.base_date,
            config.rfm.tiles,
            config.rfm.tiles,
            config.rfm.tiles,
        ],
    ).fetch_df()


def assign_customer_types(rfm: pd.DataFrame, config: Config) -> pd.DataFrame:
    """Assign one of eight customer segments based on configured thresholds."""
    r_high = (rfm["r_score"] >= config.rfm.r_threshold).astype(int)
    f_high = (rfm["f_score"] >= config.rfm.f_threshold).astype(int)
    m_high = (rfm["m_score"] >= config.rfm.m_threshold).astype(int)
    bitflags = 4 * r_high + 2 * f_high + m_high
    rfm["customer_type"] = bitflags.map(CUSTOMER_TYPES)
    return rfm


def build_statistics(rfm: pd.DataFrame) -> pd.DataFrame:
    """Build segment-level aggregate statistics."""
    return rfm.groupby("customer_type").agg(
        customers=("customer_id", "count"),
        average_recency_days=(
            "recency_days",
            lambda values: np.ceil(values.mean()).astype("int32"),
        ),
        average_frequency=(
            "frequency",
            lambda values: np.ceil(values.mean()).astype("int32"),
        ),
        average_monetary=(
            "monetary",
            lambda values: round(values.mean(), 2),
        ),
    )


def filter_dormant_customers(
    rfm: pd.DataFrame,
    config: Config,
) -> pd.DataFrame:
    """Return dormant customers matching the configured thresholds."""
    return rfm[
        (rfm["recency_days"] > config.rfm.dormant_recency_days)
        & (rfm["m_rank"] <= config.rfm.dormant_monetary_percentile)
    ].sort_values(by="monetary", ascending=False)


def save_outputs(
    rfm: pd.DataFrame,
    config: Config,
) -> None:
    """Write RFM, segment statistics, and dormant-customer files."""
    processed_dir = Path(config.paths.processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    rfm.to_csv(Path(processed_dir, config.files.rfm), index=False)
    build_statistics(rfm).to_csv(Path(processed_dir, config.files.rfm_stats))
    filter_dormant_customers(rfm, config).to_csv(
        Path(processed_dir, config.files.top_dormant),
        index=False,
    )


def run_analyze() -> None:
    config = cfg()
    input_path = Path(config.paths.interim_dir, config.files.cleaned)
    connection = create_connection()
    register_cleaned_view(connection, input_path)
    rfm = compute_rfm(connection, config)
    rfm = assign_customer_types(rfm, config)
    save_outputs(rfm, config)


if __name__ == "__main__":
    run_analyze()
