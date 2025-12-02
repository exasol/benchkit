"""Generate TPC-H supplier data in CSV format.

This module generates synthetic supplier data following the TPC-H benchmark
specification, saving the data in batches to CSV files.
"""

import argparse
import logging
import random
from typing import List, Dict, Any

from faker import Faker

from .config import (
    SUPPLIER_TOTAL_RECORDS,
    SUPPLIER_RECORDS_PER_BATCH,
    DEFAULT_OUTPUT_DIR,
    NATION_KEYS,
    ACCOUNT_BALANCE_RANGE
)
from .utils import save_batch_to_csv, calculate_batches, ensure_output_directory, setup_logging


def generate_supplier_batch(fake: Faker, batch_size: int) -> List[Dict[str, Any]]:
    """Generate a batch of supplier data.
    
    Args:
        fake: Faker instance for generating synthetic data
        batch_size: Number of supplier records to generate
        
    Returns:
        List of dictionaries containing supplier data
    """
    data = []
    for _ in range(batch_size):
        suppkey = fake.unique.random_number(digits=8)
        name = fake.company()
        address = fake.street_address()
        nationkey = random.choice(NATION_KEYS)
        phone = fake.phone_number()
        acctbal = round(random.uniform(*ACCOUNT_BALANCE_RANGE), 2)
        comment = fake.text()

        data.append({
            'suppkey': suppkey,
            'name': name,
            'address': address,
            'nationkey': nationkey,
            'phone': phone,
            'acctbal': acctbal,
            'comment': comment
        })
    return data


def generate_supplier_data(
        total_records: int = SUPPLIER_TOTAL_RECORDS,
        records_per_batch: int = SUPPLIER_RECORDS_PER_BATCH,
        output_dir: str = DEFAULT_OUTPUT_DIR
) -> None:
    """Generate supplier data and save to CSV files.
    
    Args:
        total_records: Total number of supplier records to generate
        records_per_batch: Number of records per batch
        output_dir: Directory to save output files
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info(f"Starting supplier data generation: {total_records} records in batches of {records_per_batch}")

    ensure_output_directory(output_dir)
    fake = Faker()
    num_batches = calculate_batches(total_records, records_per_batch)

    for i in range(num_batches):
        logger.info(f"Generating supplier batch {i + 1}/{num_batches}")
        batch_data = generate_supplier_batch(fake, records_per_batch)
        filename = f'supplier_batch_{i + 1}.csv'
        save_batch_to_csv(batch_data, filename, output_dir)

    logger.info(f"Supplier data generation completed. Generated {num_batches} batches.")


def main() -> None:
    """Main entry point for the supplier data generator."""
    parser = argparse.ArgumentParser(description='Generate TPC-H supplier data')
    parser.add_argument(
        '--total-records',
        type=int,
        default=SUPPLIER_TOTAL_RECORDS,
        help=f'Total number of records to generate (default: {SUPPLIER_TOTAL_RECORDS})'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=SUPPLIER_RECORDS_PER_BATCH,
        help=f'Number of records per batch (default: {SUPPLIER_RECORDS_PER_BATCH})'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f'Output directory for CSV files (default: {DEFAULT_OUTPUT_DIR})'
    )

    args = parser.parse_args()

    generate_supplier_data(
        total_records=args.total_records,
        records_per_batch=args.batch_size,
        output_dir=args.output_dir
    )


if __name__ == '__main__':
    main()
