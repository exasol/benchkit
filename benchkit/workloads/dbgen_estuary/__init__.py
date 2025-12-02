from typing import Generator, Any


class TableGenerator:
    def __init__(self, table_name: str):
        from faker import Faker
        from .customer import generate_customer_batch
        from .lineitem import generate_lineitem_batch
        from .orders import generate_orders_batch
        from .part import generate_part_batch
        from .partsupp import generate_partsupp_batch
        from .supplier import generate_supplier_batch
        from . import config as cfg

        self.fake = Faker()
        self.table_name = table_name
        self.batcher = {
            'customer': generate_customer_batch,
            'lineitem': generate_lineitem_batch,
            'orders': generate_orders_batch,
            'part': generate_part_batch,
            'partsupp': generate_partsupp_batch,
            'supplier': generate_supplier_batch,
        }[table_name]
        self.total_rows = {
            'customer': cfg.CUSTOMER_TOTAL_RECORDS,
            'lineitem': cfg.LINEITEM_TOTAL_RECORDS,
            'orders': cfg.ORDERS_TOTAL_RECORDS,
            'part': cfg.PART_TOTAL_RECORDS,
            'partsupp': cfg.PARTSUPP_TOTAL_RECORDS,
            'supplier': cfg.SUPPLIER_TOTAL_RECORDS,
        }[table_name]

    def rows(self) -> Generator[list[Any], None, None]:
        from . import config as cfg

        remaining_rows: int = self.total_rows
        while remaining_rows > 0:
            batch_rows: int = min(cfg.DEFAULT_RECORDS_PER_BATCH, remaining_rows)
            buffer = self.batcher(
                self.fake,
                batch_rows
            )
            remaining_rows -= batch_rows

            for row in buffer:
                yield (
                    # lucky for us, this produces stable value ordering
                    [v for v in row.values()]
                )
