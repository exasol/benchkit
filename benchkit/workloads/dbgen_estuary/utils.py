"""Utility functions for TPC-H data generation."""

import logging
import os
import random
from datetime import datetime, timedelta
from typing import Any


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging for the data generation process."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def random_date(start: datetime, end: datetime) -> datetime:
    """Generate a random date between start and end dates.

    Args:
        start: The earliest possible date
        end: The latest possible date

    Returns:
        A random datetime between start and end
    """
    days_between = (end - start).days
    random_days = random.randint(0, days_between)
    return start + timedelta(days=random_days)


def ensure_output_directory(output_dir: str) -> None:
    """Ensure the output directory exists, create if it doesn't.

    Args:
        output_dir: Path to the output directory

    Raises:
        OSError: If directory cannot be created
    """
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
            logging.info(f"Created output directory: {output_dir}")
        except OSError as e:
            logging.error(f"Failed to create output directory {output_dir}: {e}")
            raise


def save_batch_to_csv(
    data: list[dict[str, Any]], filename: str, output_dir: str
) -> None:
    """Save a batch of data to CSV file.

    Args:
        data: List of dictionaries containing the data
        filename: Name of the output file
        output_dir: Directory to save the file in

    Raises:
        Exception: If file cannot be written
    """
    import pandas as pd

    try:
        df = pd.DataFrame(data)
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, index=False)
        logging.info(f"Saved {len(data)} records to {filepath}")
    except Exception as e:
        logging.error(f"Failed to save batch to {filename}: {e}")
        raise


def calculate_batches(total_records: int, records_per_batch: int) -> int:
    """Calculate the number of batches needed.

    Args:
        total_records: Total number of records to generate
        records_per_batch: Number of records per batch

    Returns:
        Number of batches needed
    """
    return total_records // records_per_batch
