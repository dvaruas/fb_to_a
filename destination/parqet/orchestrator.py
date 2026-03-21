import csv
import logging
import os
import typing

import source.scalable
from destination.parqet.config import Config
from destination.parqet.models import Transaction
from destination.parqet.source_scalable import from_scalable_transaction

_module_logger = logging.getLogger(__name__)


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
        self.logger = _module_logger

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
                transaction = from_scalable_transaction(transaction_detail, self.logger)
                if transaction is None:
                    skipped += 1
                    continue

                row = transaction.as_record()
                writer.writerow(row)
                processed += 1
                # currency_v = transaction_detail.currency
                # event_datetime = transaction_detail.event_datetime
                # fee_v = transaction_detail.total_fee

                # if transaction_detail.type == source.scalable.TransactionType.SECURITY:
                #     pass
                # elif transaction_detail.type == source.scalable.TransactionType.CASH:
                #     # ignore CASH_TRANSACTION, not sure how to structure these values in CSV
                #     # print(
                #     #     f"[{transaction_id}] Skipping transaction due to type = cash..."
                #     # )
                #     # TODO: we would need to consider these cash transactions for the purpose of distributions
                #     skipped += 1
                #     continue
                # elif (
                #     transaction_detail.type
                #     == source.scalable.TransactionType.NON_TRADE_SECURITY
                # ):
                #     # ignore NON_TRADE_SECURITY_TRANSACTION, these are just internal reorgs
                #     print(
                #         f"[{transaction_detail.id}] Skipping transaction due to type = non_security_transaction..."
                #     )
                #     skipped += 1
                #     continue
                # else:
                #     raise ValueError(
                #         f"[{transaction_detail.id}] Unknown transaction type: {transaction_detail.type}"
                #     )

                # if transaction_detail.is_pending or transaction_detail.is_cancellation:
                #     print(
                #         f"[{transaction_detail.id}] Skipping transaction due to pending or cancelled status..."
                #     )
                #     skipped += 1
                #     continue

                # # dt = datetime.strptime(
                # #     transaction_details["lastEventDateTime"],
                # #     "%Y-%m-%dT%H:%M:%S.%fZ",
                # # ).replace(tzinfo=timezone.utc)
                # datetime_v = (
                #     event_datetime.strftime("%Y-%m-%dT%H:%M:%S.")
                #     + f"{event_datetime.microsecond // 1000:03d}Z"
                # )

                # # transacton_fee = (
                # #     transaction_details["tradeTransactionAmounts"]["transactionFee"]
                # #     or 0.0
                # # )
                # # venue_fee = (
                # #     transaction_details["tradeTransactionAmounts"]["venueFee"]
                # #     or 0.0
                # # )
                # # crypto_spread_fee = (
                # #     transaction_details["tradeTransactionAmounts"][
                # #         "cryptoSpreadFee"
                # #     ]
                # #     or 0.0
                # # )
                # # fee_v = transacton_fee + venue_fee + crypto_spread_fee

                # identifier_v = transaction_detail.isin

                # price_v = transaction_detail.average_price

                # shares_v = transaction_detail.total_shares

                # amount_v = 0.0
                # if transaction_detail.side == "BUY":
                #     amount_v = -transaction_details["totalAmount"]
                # elif transaction_details["side"] == "SELL":
                #     amount_v = transaction_details["totalAmount"]
                # else:
                #     raise ValueError(
                #         f"[{transaction_id}] Unknown transaction side : {transaction_details['side']}"
                #     )

                # # tax_v = transaction_details["tradeTransactionAmounts"]["taxAmount"]

                # # type_v = ""
                # # if transaction_details["side"] == "BUY":
                # #     type_v = "Buy"
                # # elif transaction_details["side"] == "SELL":
                # #     type_v = "Sell"
                # # else:
                # #     # For security transactions only Buy and Sell are valid
                # #     # Dividend , Interest = falls under Cash transactions
                # #     # TransferIn or TransferOut = falls under not_trade_security_transaction
                # #     raise ValueError(
                # #         f"[{transaction_id}] Unknown transaction side : {transaction_details['side']}"
                # #     )

                # row = {
                #     "Currency": currency_v,
                #     "datetime": datetime_v,
                #     "fee": fee_v,
                #     # "AssetType": assetType_v,
                #     "identifier": identifier_v,
                #     "price": price_v,
                #     "shares": shares_v,
                #     # "amount": amount_v,
                #     # "tax": tax_v,
                #     # "type": type_v,
                # }

            # except Exception:
            #     print("failed for file: ", file_name)
            #     raise
