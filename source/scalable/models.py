from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import AliasPath, BaseModel, Field, computed_field


class SecurityTransactionType(Enum):
    SECURITY = "SECURITY_TRANSACTION"
    CASH = "CASH_TRANSACTION"
    NON_TRADE_SECURITY = "NON_TRADE_SECURITY_TRANSACTION"


class TransactionDetailModel(BaseModel):
    id: str
    type: SecurityTransactionType
    currency: str
    event_datetime: datetime = Field(alias="lastEventDateTime")
    is_pending: bool = Field(alias="isPending")
    is_cancellation: bool = Field(alias="isCancellation")


class SecuritiesTransactionDetailModel(TransactionDetailModel):
    # Fees
    transaction_fee: Optional[float] = Field(
        default=None,
        validation_alias=AliasPath("tradeTransactionAmounts", "transactionFee"),
    )
    venue_fee: Optional[float] = Field(
        default=None, validation_alias=AliasPath("tradeTransactionAmounts", "venueFee")
    )
    crypto_spread_fee: Optional[float] = Field(
        default=None,
        validation_alias=AliasPath("tradeTransactionAmounts", "cryptoSpreadFee"),
    )

    @computed_field
    @property
    def total_fee(self) -> float:
        return sum(
            v or 0
            for v in (self.transaction_fee, self.venue_fee, self.crypto_spread_fee)
        )

    isin: Optional[str] = Field(
        default=None, validation_alias=AliasPath("security", "isin")
    )
    average_price: Optional[float] = Field(
        default=None, validation_alias=AliasPath("averagePrice")
    )
    total_shares: Optional[float] = Field(
        default=None, validation_alias=AliasPath("numberOfShares", "total")
    )


class TransactionOverviewModel(BaseModel):
    id: str


class TransactionsPageModel(BaseModel):
    cursor: Optional[str] = None
    total: int
    transactions: List[TransactionOverviewModel]
