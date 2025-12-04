"""Configuration constants for TPC-H data generation."""

from typing import List

# Batch configuration
DEFAULT_RECORDS_PER_BATCH = 1000
DEFAULT_OUTPUT_DIR = "."

# Table-specific record counts
CUSTOMER_TOTAL_RECORDS = 15000000
LINEITEM_TOTAL_RECORDS = 600000000
ORDERS_TOTAL_RECORDS = 150000000
PART_TOTAL_RECORDS = 20000000
PARTSUPP_TOTAL_RECORDS = 80000000
SUPPLIER_TOTAL_RECORDS = 1000000

# Supplier batch size is different (smaller)
SUPPLIER_RECORDS_PER_BATCH = 100000

# Date ranges
START_DATE = "1992-01-01"
END_DATE = "1998-12-31"

# Domain values
NATION_KEYS: List[int] = list(range(1, 26))  # 25 nations
CUSTOMER_SEGMENTS: List[str] = [
    "AUTOMOBILE",
    "BUILDING",
    "FURNITURE",
    "HOUSEHOLD",
    "MACHINERY",
]

# Orders
ORDER_STATUSES: List[str] = ["O", "F", "P"]
ORDER_PRIORITIES: List[str] = [
    "1-URGENT",
    "2-HIGH",
    "3-MEDIUM",
    "4-NOT SPECIFIED",
    "5-LOW",
]

# Line items
RETURN_FLAGS: List[str] = ["R", "A", "N"]
LINE_STATUSES: List[str] = ["O", "F"]
SHIP_INSTRUCTIONS: List[str] = [
    "DELIVER IN PERSON",
    "COLLECT COD",
    "TAKE BACK RETURN",
    "NONE",
]
SHIP_MODES: List[str] = ["TRUCK", "MAIL", "SHIP", "RAIL", "AIR", "FOB", "REG AIR"]

# Parts
MANUFACTURERS: List[str] = [
    "Manufacturer#1",
    "Manufacturer#2",
    "Manufacturer#3",
    "Manufacturer#4",
    "Manufacturer#5",
]
BRANDS: List[str] = ["Brand#1", "Brand#2", "Brand#3", "Brand#4", "Brand#5"]
PART_TYPES: List[str] = ["Type#1", "Type#2", "Type#3", "Type#4", "Type#5"]
PART_SIZES: List[int] = [1, 2, 3, 4, 5, 6, 7, 8]
CONTAINERS: List[str] = [
    "SM CASE",
    "SM BOX",
    "SM PACK",
    "SM PKG",
    "LG CASE",
    "LG BOX",
    "LG PACK",
    "LG PKG",
]

# Value ranges
ACCOUNT_BALANCE_RANGE = (-999.99, 9999.99)
PART_RETAIL_PRICE_RANGE = (900.00, 2000.00)
ORDER_TOTAL_PRICE_RANGE = (100.00, 500000.00)
LINEITEM_EXTENDED_PRICE_RANGE = (100.00, 100000.00)
DISCOUNT_RANGE = (0.00, 0.10)
TAX_RANGE = (0.00, 0.08)
SUPPLY_COST_RANGE = (1.00, 1000.00)
QUANTITY_RANGE = (1, 50)
AVAILABILITY_QTY_RANGE = (1, 10000)
LINE_NUMBER_RANGE = (1, 7)
SHIP_PRIORITY_RANGE = (0, 1)
