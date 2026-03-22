import logging


class TransactionsPageLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        page_no = self.extra["page_no"] if self.extra is not None else "UNKNOWN"
        return f"[txns_page {page_no}] {msg}", kwargs

    @classmethod
    def get_logger(cls, logger: logging.Logger, page_no: int) -> logging.LoggerAdapter:
        return cls(logger, extra={"page_no": page_no})


class TransactionLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        transaction_id = (
            self.extra["transaction_id"] if self.extra is not None else "UNKNOWN"
        )
        return f"[txn {transaction_id}] {msg}", kwargs

    @classmethod
    def get_logger(
        cls, logger: logging.Logger, transaction_id: str
    ) -> logging.LoggerAdapter:
        return cls(
            logger,
            extra={
                "transaction_id": (
                    transaction_id
                    if len(transaction_id) <= 13
                    else f"{transaction_id[:10]}...{transaction_id[-3:]}"
                )
            },
        )
