import datetime
import enum
import typing

import pydantic


class TransactionType(str, enum.Enum):
    SECURITY = "SECURITY_TRANSACTION"
    CASH = "CASH_TRANSACTION"
    NON_TRADE_SECURITY = "NON_TRADE_SECURITY_TRANSACTION"


class TransactionSide(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class TransactionDetailModel(pydantic.BaseModel):
    id: str
    type: TransactionType
    currency: str
    event_datetime: datetime.datetime = pydantic.Field(alias="lastEventDateTime")
    is_pending: bool = pydantic.Field(alias="isPending")
    is_cancellation: bool = pydantic.Field(alias="isCancellation")


class SecuritiesTransactionDetailModel(TransactionDetailModel):
    type: typing.Literal[TransactionType.SECURITY]

    # Details
    side: TransactionSide
    isin: typing.Optional[str] = pydantic.Field(
        default=None, validation_alias=pydantic.AliasPath("security", "isin")
    )
    average_price: typing.Optional[float] = pydantic.Field(
        default=None, validation_alias=pydantic.AliasPath("averagePrice")
    )
    total_shares: typing.Optional[float] = pydantic.Field(
        default=None, validation_alias=pydantic.AliasPath("numberOfShares", "total")
    )
    total_amount: typing.Optional[float] = pydantic.Field(
        default=None, validation_alias=pydantic.AliasPath("totalAmount")
    )

    # Fees
    transaction_fee: typing.Optional[float] = pydantic.Field(
        default=None,
        validation_alias=pydantic.AliasPath(
            "tradeTransactionAmounts", "transactionFee"
        ),
    )
    venue_fee: typing.Optional[float] = pydantic.Field(
        default=None,
        validation_alias=pydantic.AliasPath("tradeTransactionAmounts", "venueFee"),
    )
    crypto_spread_fee: typing.Optional[float] = pydantic.Field(
        default=None,
        validation_alias=pydantic.AliasPath(
            "tradeTransactionAmounts", "cryptoSpreadFee"
        ),
    )

    @pydantic.computed_field
    @property
    def total_fee(self) -> float:
        return sum(
            v or 0
            for v in (self.transaction_fee, self.venue_fee, self.crypto_spread_fee)
        )

    # Tax
    tax: typing.Optional[float] = pydantic.Field(
        default=0.0,
        validation_alias=pydantic.AliasPath("tradeTransactionAmounts", "taxAmount"),
    )


class CashTransactionDetailModel(TransactionDetailModel):
    type: typing.Literal[TransactionType.CASH]


class NonTradeSecurityTransactionDetailModel(TransactionDetailModel):
    type: typing.Literal[TransactionType.NON_TRADE_SECURITY]


AnyTransactionDetailModel = typing.Annotated[
    typing.Union[
        SecuritiesTransactionDetailModel,
        CashTransactionDetailModel,
        NonTradeSecurityTransactionDetailModel,
    ],
    pydantic.Field(discriminator="type"),
]


class TransactionOverviewModel(pydantic.BaseModel):
    id: str


class TransactionsPageModel(pydantic.BaseModel):
    cursor: typing.Optional[str] = None
    total: int
    transactions: typing.List[TransactionOverviewModel]
