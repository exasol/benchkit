"""Generate TPC-H orders data in CSV format.

This module generates synthetic orders data following the TPC-H benchmark
specification, saving the data in batches to CSV files.
"""

import argparse
import logging
import random
from datetime import datetime
from typing import List, Dict, Any

from faker import Faker

from .config import (
    ORDERS_TOTAL_RECORDS,
    DEFAULT_RECORDS_PER_BATCH,
    DEFAULT_OUTPUT_DIR,
    ORDER_STATUSES,
    ORDER_PRIORITIES,
    ORDER_TOTAL_PRICE_RANGE,
    SHIP_PRIORITY_RANGE,
    START_DATE,
    END_DATE
)
from .utils import save_batch_to_csv, calculate_batches, ensure_output_directory, setup_logging, random_date


def generate_orders_batch(fake: Faker, batch_size: int) -> List[Dict[str, Any]]:
    """Generate a batch of orders data.
    
    Args:
        fake: Faker instance for generating synthetic data
        batch_size: Number of orders records to generate
        
    Returns:
        List of dictionaries containing orders data
    """
    data = []
    start_date = datetime.strptime(START_DATE, '%Y-%m-%d')
    end_date = datetime.strptime(END_DATE, '%Y-%m-%d')

    for _ in range(batch_size):
        orderkey = fake.unique.random_number(digits=8)
        custkey = fake.unique.random_number(digits=8)
        orderstatus = random.choice(ORDER_STATUSES)
        totalprice = round(random.uniform(*ORDER_TOTAL_PRICE_RANGE), 2)
        orderdate = random_date(start_date, end_date)
        orderpriority = random.choice(ORDER_PRIORITIES)
        clerk = fake.name()
        shippriority = random.randint(*SHIP_PRIORITY_RANGE)
        comment = fake.text()

        data.append({
            'orderkey': orderkey,
            'custkey': custkey,
            'orderstatus': orderstatus,
            'totalprice': totalprice,
            'orderdate': orderdate.strftime('%Y-%m-%d'),
            'orderpriority': orderpriority,
            'clerk': clerk,
            'shippriority': shippriority,
            'comment': comment
        })
    return data


def generate_orders_data(
        total_records: int = ORDERS_TOTAL_RECORDS,
        records_per_batch: int = DEFAULT_RECORDS_PER_BATCH,
        output_dir: str = DEFAULT_OUTPUT_DIR
) -> None:
    """Generate orders data and save to CSV files.
    
    Args:
        total_records: Total number of orders records to generate
        records_per_batch: Number of records per batch
        output_dir: Directory to save output files
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info(f"Starting orders data generation: {total_records} records in batches of {records_per_batch}")

    ensure_output_directory(output_dir)
    fake = Faker()
    num_batches = calculate_batches(total_records, records_per_batch)

    for i in range(num_batches):
        logger.info(f"Generating orders batch {i + 1}/{num_batches}")
        batch_data = generate_orders_batch(fake, records_per_batch)
        filename = f'orders_batch_{i + 1}.csv'
        save_batch_to_csv(batch_data, filename, output_dir)

    logger.info(f"Orders data generation completed. Generated {num_batches} batches.")


def main() -> None:
    """Main entry point for the orders data generator."""
    parser = argparse.ArgumentParser(description='Generate TPC-H orders data')
    parser.add_argument(
        '--total-records',
        type=int,
        default=ORDERS_TOTAL_RECORDS,
        help=f'Total number of records to generate (default: {ORDERS_TOTAL_RECORDS})'
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

    generate_orders_data(
        total_records=args.total_records,
        records_per_batch=args.batch_size,
        output_dir=args.output_dir
    )


if __name__ == '__main__':
    main()
