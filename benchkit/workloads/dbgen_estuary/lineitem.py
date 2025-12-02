"""Generate TPC-H lineitem data in CSV format.

This module generates synthetic lineitem data following the TPC-H benchmark
specification, saving the data in batches to CSV files.
"""

import argparse
import logging
import random
from datetime import datetime
from typing import List, Dict, Any

from faker import Faker

from .config import (
    LINEITEM_TOTAL_RECORDS,
    DEFAULT_RECORDS_PER_BATCH,
    DEFAULT_OUTPUT_DIR,
    RETURN_FLAGS,
    LINE_STATUSES,
    SHIP_INSTRUCTIONS,
    SHIP_MODES,
    LINEITEM_EXTENDED_PRICE_RANGE,
    DISCOUNT_RANGE,
    TAX_RANGE,
    QUANTITY_RANGE,
    LINE_NUMBER_RANGE,
    START_DATE,
    END_DATE
)
from .utils import save_batch_to_csv, calculate_batches, ensure_output_directory, setup_logging, random_date


def generate_lineitem_batch(fake: Faker, batch_size: int) -> List[Dict[str, Any]]:
    """Generate a batch of lineitem data.
    
    Args:
        fake: Faker instance for generating synthetic data
        batch_size: Number of lineitem records to generate
        
    Returns:
        List of dictionaries containing lineitem data
    """
    data = []
    start_date = datetime.strptime(START_DATE, '%Y-%m-%d')
    end_date = datetime.strptime(END_DATE, '%Y-%m-%d')

    for _ in range(batch_size):
        orderkey = fake.unique.random_number(digits=8)
        partkey = fake.unique.random_number(digits=8)
        suppkey = fake.unique.random_number(digits=8)
        linenumber = random.randint(*LINE_NUMBER_RANGE)
        quantity = random.randint(*QUANTITY_RANGE)
        extendedprice = round(random.uniform(*LINEITEM_EXTENDED_PRICE_RANGE), 2)
        discount = round(random.uniform(*DISCOUNT_RANGE), 2)
        tax = round(random.uniform(*TAX_RANGE), 2)
        returnflag = random.choice(RETURN_FLAGS)
        linestatus = random.choice(LINE_STATUSES)
        shipdate = random_date(start_date, end_date)
        commitdate = random_date(shipdate, end_date)
        receiptdate = random_date(commitdate, end_date)
        shipinstruct = random.choice(SHIP_INSTRUCTIONS)
        shipmode = random.choice(SHIP_MODES)
        comment = fake.text()

        data.append({
            'orderkey': orderkey,
            'partkey': partkey,
            'suppkey': suppkey,
            'linenumber': linenumber,
            'quantity': quantity,
            'extendedprice': extendedprice,
            'discount': discount,
            'tax': tax,
            'returnflag': returnflag,
            'linestatus': linestatus,
            'shipdate': shipdate.strftime('%Y-%m-%d'),
            'commitdate': commitdate.strftime('%Y-%m-%d'),
            'receiptdate': receiptdate.strftime('%Y-%m-%d'),
            'shipinstruct': shipinstruct,
            'shipmode': shipmode,
            'comment': comment
        })
    return data


def generate_lineitem_data(
        total_records: int = LINEITEM_TOTAL_RECORDS,
        records_per_batch: int = DEFAULT_RECORDS_PER_BATCH,
        output_dir: str = DEFAULT_OUTPUT_DIR
) -> None:
    """Generate lineitem data and save to CSV files.
    
    Args:
        total_records: Total number of lineitem records to generate
        records_per_batch: Number of records per batch
        output_dir: Directory to save output files
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info(f"Starting lineitem data generation: {total_records} records in batches of {records_per_batch}")

    ensure_output_directory(output_dir)
    fake = Faker()
    num_batches = calculate_batches(total_records, records_per_batch)

    for i in range(num_batches):
        logger.info(f"Generating lineitem batch {i + 1}/{num_batches}")
        batch_data = generate_lineitem_batch(fake, records_per_batch)
        filename = f'lineitem_batch_{i + 1}.csv'
        save_batch_to_csv(batch_data, filename, output_dir)

    logger.info(f"Lineitem data generation completed. Generated {num_batches} batches.")


def main() -> None:
    """Main entry point for the lineitem data generator."""
    parser = argparse.ArgumentParser(description='Generate TPC-H lineitem data')
    parser.add_argument(
        '--total-records',
        type=int,
        default=LINEITEM_TOTAL_RECORDS,
        help=f'Total number of records to generate (default: {LINEITEM_TOTAL_RECORDS})'
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

    generate_lineitem_data(
        total_records=args.total_records,
        records_per_batch=args.batch_size,
        output_dir=args.output_dir
    )


if __name__ == '__main__':
    main()
