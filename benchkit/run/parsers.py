"""Result parsing and normalization utilities."""

from typing import Any

import pandas as pd


def normalize_runs(results: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Normalize benchmark results into a standard DataFrame format.

    Args:
        results: List of raw benchmark results

    Returns:
        Normalized DataFrame with standardized columns
    """
    if not results:
        return pd.DataFrame()

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Ensure required columns exist
    required_columns = ["system", "query_name", "elapsed_s"]
    for col in required_columns:
        if col not in df.columns:
            if col == "query_name" and "query" in df.columns:
                df["query_name"] = df["query"]
            elif col == "system" and "system_name" in df.columns:
                df["system"] = df["system_name"]
            else:
                df[col] = None

    # Add derived columns
    df["elapsed_ms"] = (df["elapsed_s"] * 1000).round(1)

    # Rename columns for consistency
    column_mapping = {
        "query_name": "query",
        "run_number": "run",
    }
    df = df.rename(columns=column_mapping)

    # Select and order final columns
    final_columns = ["system", "query", "run", "elapsed_s", "elapsed_ms"]

    # Add optional columns if they exist
    optional_columns = [
        "stream_id",
        "rows_returned",
        "success",
        "error",
        "workload",
        "scale_factor",
        "variant",
    ]
    for col in optional_columns:
        if col in df.columns:
            final_columns.append(col)

    # Filter to existing columns
    final_columns = [col for col in final_columns if col in df.columns]

    return df[final_columns]
