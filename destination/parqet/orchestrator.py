import csv
import logging
import os
import typing

import source.scalable
from destination.parqet.config import Config
from destination.parqet.models import Transaction
from destination.parqet.source_scalable import from_scalable_transaction


class Orchestrator:
    config: Config
    logger: logging.Logger

    _field_names = [
        "Currency",  # eg: EUR
        "datetime",  # yyyy-MM-ddTHH:mm:ss.fffZ, eg: 2021-11-07T18:25:21.689Z
        "fee",  # trade fees, eg: 1.00
        "AssetType",  # v = Security , Crypto or Cash
        "identifier",  # isin / crypto symbol
        "price",  # per share price, eg: 1.00
        "shares",  # total number of shares, eg: 1.00
        "amount",  # transaction total eg: 1.00
        "tax",  # total tax amount, eg: 1.00
        "type",  # v = Buy , Sell , Dividend , Interest , TransferIn or TransferOut"
    ]

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def from_source_scalable(self, source_orchestrator: source.scalable.Orchestrator):
        if os.path.exists(self.config.params.output_path):
            os.remove(self.config.params.output_path)

        with open(
            self.config.params.output_path, "w", newline="", encoding="utf-8"
        ) as fw:
            writer = csv.DictWriter(
                fw,
                fieldnames=Orchestrator._field_names,
            )
            writer.writeheader()

            skipped = 0
            processed = 0

            for transaction_detail in source_orchestrator.get_transactions_details():
                transaction = from_scalable_transaction(transaction_detail)
                if transaction is None:
                    skipped += 1
                    continue

                row = transaction.as_record()
                writer.writerow(row)
                processed += 1

            self.logger.info(
                f"processed {processed} transactions and skipped {skipped} transactions"
            )
