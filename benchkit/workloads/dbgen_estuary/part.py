"""Generate TPC-H part data in CSV format.

This module generates synthetic part data following the TPC-H benchmark
specification, saving the data in batches to CSV files.
"""

import argparse
import logging
import random
from typing import List, Dict, Any

from faker import Faker

from .config import (
    PART_TOTAL_RECORDS,
    DEFAULT_RECORDS_PER_BATCH,
    DEFAULT_OUTPUT_DIR,
    MANUFACTURERS,
    BRANDS,
    PART_TYPES,
    PART_SIZES,
    CONTAINERS,
    PART_RETAIL_PRICE_RANGE
)
from .utils import save_batch_to_csv, calculate_batches, ensure_output_directory, setup_logging


def generate_part_batch(fake: Faker, batch_size: int) -> List[Dict[str, Any]]:
    """Generate a batch of part data.
    
    Args:
        fake: Faker instance for generating synthetic data
        batch_size: Number of part records to generate
        
    Returns:
        List of dictionaries containing part data
    """
    data = []
    for _ in range(batch_size):
        partkey = fake.unique.random_number(digits=8)
        name = f"Part#{fake.unique.random_number(digits=6)}"
        manufacturer = random.choice(MANUFACTURERS)
        brand = random.choice(BRANDS)
        part_type = random.choice(PART_TYPES)
        size = random.choice(PART_SIZES)
        container = random.choice(CONTAINERS)
        retailprice = round(random.uniform(*PART_RETAIL_PRICE_RANGE), 2)
        comment = fake.text()

        data.append({
            'partkey': partkey,
            'name': name,
            'manufacturer': manufacturer,
            'brand': brand,
            'type': part_type,
            'size': size,
            'container': container,
            'retailprice': retailprice,
            'comment': comment
        })
    return data


def generate_part_data(
        total_records: int = PART_TOTAL_RECORDS,
        records_per_batch: int = DEFAULT_RECORDS_PER_BATCH,
        output_dir: str = DEFAULT_OUTPUT_DIR
) -> None:
    """Generate part data and save to CSV files.
    
    Args:
        total_records: Total number of part records to generate
        records_per_batch: Number of records per batch
        output_dir: Directory to save output files
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info(f"Starting part data generation: {total_records} records in batches of {records_per_batch}")

    ensure_output_directory(output_dir)
    fake = Faker()
    num_batches = calculate_batches(total_records, records_per_batch)

    for i in range(num_batches):
        logger.info(f"Generating part batch {i + 1}/{num_batches}")
        batch_data = generate_part_batch(fake, records_per_batch)
        filename = f'part_batch_{i + 1}.csv'
        save_batch_to_csv(batch_data, filename, output_dir)

    logger.info(f"Part data generation completed. Generated {num_batches} batches.")


def main() -> None:
    """Main entry point for the part data generator."""
    parser = argparse.ArgumentParser(description='Generate TPC-H part data')
    parser.add_argument(
        '--total-records',
        type=int,
        default=PART_TOTAL_RECORDS,
        help=f'Total number of records to generate (default: {PART_TOTAL_RECORDS})'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=DEFAULT_RECORDS_PER_BATCH,
        help=f'Number of records per batch (default: {DEFAULT_RECORDS_PER_BATCH})'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f'Output directory for CSV files (default: {DEFAULT_OUTPUT_DIR})'
    )

    args = parser.parse_args()

    generate_part_data(
        total_records=args.total_records,
        records_per_batch=args.batch_size,
        output_dir=args.output_dir
    )


if __name__ == '__main__':
    main()
