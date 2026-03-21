import logging
import typing

import source.scalable
from destination.parqet.models import AssetType, Transaction, TransactionType


def from_scalable_transaction(
    txn: source.scalable.TransactionDetailModel,
    logger: logging.Logger,
) -> typing.Optional[Transaction]:
    if txn.is_pending or txn.is_cancellation:
        logger.info(
            f"[{txn.id}] Skipping transaction due to pending or cancelled status..."
        )
        return None

    if isinstance(txn, source.scalable.SecuritiesTransactionDetailModel):
        return from_scalable_securities_transaction(txn)
    elif isinstance(txn, source.scalable.CashTransactionDetailModel):
        return from_scalable_cash_transaction(txn)
    else:
        # ignore NON_TRADE_SECURITY_TRANSACTION, these are just internal reorgs
        logger.info(f"[{txn.id}] Skipping transaction due to type = {txn.type}...")
        return None


def from_scalable_securities_transaction(
    txn: source.scalable.SecuritiesTransactionDetailModel,
) -> Transaction:
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
) -> typing.Optional[Transaction]:
    # TODO: add the dividends calculation part here
    # print(
    #     f"[{transaction_id}] Skipping transaction due to type = cash..."
    # )
    # TODO: we would need to consider these cash transactions for the purpose of distributions
    return None
