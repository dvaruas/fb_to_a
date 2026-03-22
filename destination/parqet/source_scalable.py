import logging
import typing

import source.scalable
from destination.parqet.models import AssetType, Transaction, TransactionType


def from_scalable_transaction(
    txn: source.scalable.TransactionDetailModel,
) -> typing.Optional[Transaction]:
    logger = source.scalable.TransactionLoggerAdapter.get_logger(
        logging.getLogger(__name__), txn.id
    )
    if txn.is_pending or txn.is_cancellation:
        logger.debug("skipping transaction due to pending or cancelled status...")
        return None

    if isinstance(txn, source.scalable.SecuritiesTransactionDetailModel):
        return from_scalable_securities_transaction(txn, logger)
    elif isinstance(txn, source.scalable.CashTransactionDetailModel):
        return from_scalable_cash_transaction(txn, logger)
    else:
        # ignore NON_TRADE_SECURITY_TRANSACTION, these are just internal reorgs
        logger.debug(f"skipping transaction due to type = {txn.type}...")
        return None


def from_scalable_securities_transaction(
    txn: source.scalable.SecuritiesTransactionDetailModel,
    logger: logging.Logger,
) -> Transaction:
    if txn.status != source.scalable.TransactionStatus.FINAL_FILL:
        logger.debug(f"skipping transaction due to status {txn.status}...")
        return None

    amount_v = (
        txn.total_amount
        if txn.side == source.scalable.TransactionSide.SELL
        else -txn.total_amount
    )
    transaction_type_v = (
        TransactionType.BUY
        if txn.side == source.scalable.TransactionSide.BUY
        else TransactionType.SELL
    )

    if amount_v == 0.0 or txn.average_price == 0.0 or txn.total_shares == 0.0:
        raise ValueError(
            f"something related to amount is wrong with this transaction: {txn.id}"
        )

    return Transaction(
        currency=txn.currency,
        execution_time=txn.event_datetime,
        fee=txn.total_fee,
        asset_type=AssetType.SECURITY,
        identifier=txn.isin,
        price=txn.average_price,
        shares=txn.total_shares,
        amount=amount_v,
        tax=txn.tax,
        transaction_type=transaction_type_v,
    )


def from_scalable_cash_transaction(
    txn: source.scalable.CashTransactionDetailModel,
    logger: logging.Logger,
) -> typing.Optional[Transaction]:
    # Only consider distributions / dividends
    if txn.transaction_type != source.scalable.CashTransactionType.DISTRIBUTION:
        logger.debug(
            f"skipping cash transaction due to type = {txn.transaction_type}..."
        )
        return None

    amount = txn.tax_gross_amount or txn.amount
    if amount == 0.0:
        raise ValueError(
            f"something related to amount is wrong with this transaction: {txn.id}"
        )

    return Transaction(
        currency=txn.currency,
        execution_time=txn.event_datetime,
        fee=0,
        asset_type=AssetType.SECURITY,
        identifier=txn.isin,
        price=amount,
        shares=1,
        amount=amount,
        tax=txn.tax,
        transaction_type=TransactionType.DIVIDEND,
    )
