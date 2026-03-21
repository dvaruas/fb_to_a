import dataclasses
import datetime
import enum
import typing


class AssetType(enum.Enum):
    SECURITY = "Security"
    CRYPTO = "Crypto"
    CASH = "Cash"


class TransactionType(enum.Enum):
    BUY = "Buy"
    SELL = "Sell"
    DIVIDEND = "Dividend"
    INTEREST = "Interest"
    TRANSFER_IN = "TransferIn"
    TRANSFER_OUT = "TransferOut"


@dataclasses.dataclass
class Transaction:
    currency: str
    execution_time: datetime.datetime
    fee: float
    asset_type: AssetType
    identifier: str
    price: float
    shares: float
    amount: float
    tax: float
    transaction_type: TransactionType

    def as_record(self) -> dict[str, typing.Any]:
        execution_time_str = (
            self.execution_time.strftime("%Y-%m-%dT%H:%M:%S.")
            + f"{self.execution_time.microsecond // 1000:03d}Z"
        )

        return {
            "Currency": self.currency,
            "datetime": execution_time_str,
            "fee": self.fee,
            "AssetType": self.asset_type.value,
            "identifier": self.identifier,
            "price": self.price,
            "shares": self.shares,
            "amount": self.amount,
            "tax": self.tax,
            "type": self.transaction_type.value,
        }
