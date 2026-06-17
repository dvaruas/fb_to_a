import json
import logging
import os
import pathlib
import shutil
import typing

import pydantic
import requests

from source.scalable.config import Config
from source.scalable.loggers import (
    TransactionLoggerAdapter,
    TransactionsPageLoggerAdapter,
)
from source.scalable.models import (
    AnyTransactionDetailModel,
    TransactionDetailModel,
    TransactionsPageModel,
)
from utils.with_duration import run_with_duration

transactions_page_size = 200


class _Transaction:
    transaction_id: str
    config: Config
    logger: logging.LoggerAdapter
    data: typing.Optional[TransactionDetailModel]
    raw_data: typing.Optional[typing.Any]
    fetch_duration: float
    save_duration: float

    def __init__(
        self, transaction_id: str, config: Config, ignore_previous: bool = False
    ):
        self.transaction_id = transaction_id
        self.config = config
        self.logger = TransactionLoggerAdapter.get_logger(
            logging.getLogger(__name__), transaction_id
        )
        self.data = None
        self.raw_data = None
        self.fetch_duration = 0.0
        self.save_duration = 0.0

        if not ignore_previous:
            self.__load_cached_data()

    def get_file_path(self) -> pathlib.Path:
        return (
            self.config.params.output_path
            / "data_points"
            / f"txn_{self.transaction_id}.json"
        )

    def __load_cached_data(self) -> None:
        file_path = self.get_file_path()
        if not file_path.exists():
            return
        with open(file_path, "r") as fr:
            self.raw_data = json.load(fr)
            self.data = self._extract_model_from_json()
        self.logger.debug("data loaded from disk")

    def _extract_model_from_json(self) -> TransactionDetailModel:
        if self.raw_data is None:
            raise Exception("no raw_data found for model")
        raw_detail = self.raw_data[0]["data"]["account"]["brokerPortfolio"][
            "transactionDetails"
        ]
        return pydantic.TypeAdapter(AnyTransactionDetailModel).validate_python(
            raw_detail
        )

    @run_with_duration("fetch_duration")
    def fetch(self) -> None:
        if self.data is not None:
            return

        payload_raw = (
            '[{"operationName":"getTransactionDetails","variables":{"personId":"'
            + self.config.params.person_id
            + '","transactionId":"'
            + self.transaction_id
            + '","portfolioId":"'
            + self.config.params.portfolio_id
            + '"},"query":"query getTransactionDetails($personId: ID\u0021, $transactionId: ID\u0021, $portfolioId: ID\u0021) {\\n  account(id: $personId) {\\n    id\\n    brokerPortfolio(id: $portfolioId) {\\n      id\\n      transactionDetails(id: $transactionId) {\\n        ...TransactionDetailsFragment\\n        __typename\\n      }\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n\\nfragment TransactionDetailsFragment on BrokerTransaction {\\n  id\\n  currency\\n  type\\n  documents {\\n    id\\n    url\\n    label\\n    __typename\\n  }\\n  lastEventDateTime\\n  isPending\\n  isCancellation\\n  security {\\n    ...SecurityNameOnlyFragment\\n    __typename\\n  }\\n  transactionReference\\n  ...SecurityTransactionDetailsFragment\\n  ...CashTransactionDetailsFragment\\n  ...NonTradeSecurityTransactionDetailsFragment\\n  ...EltifTransactionDetailsFragment\\n  __typename\\n}\\n\\nfragment SecurityNameOnlyFragment on Security {\\n  id\\n  name\\n  isin\\n  __typename\\n}\\n\\nfragment SecurityTransactionDetailsFragment on BrokerSecurityTransaction {\\n  id\\n  side\\n  status\\n  numberOfShares {\\n    filled\\n    total\\n    __typename\\n  }\\n  averagePrice\\n  totalAmount\\n  finalisationReason\\n  limitPrice\\n  stopPrice\\n  validUntil\\n  isCancellationRequested\\n  tradeTransactionAmounts {\\n    marketValuation\\n    taxAmount\\n    transactionFee\\n    venueFee\\n    cryptoSpreadFee\\n    __typename\\n  }\\n  tradingVenue\\n  fee\\n  transactionalFee\\n  taxes\\n  securityTransactionHistory: transactionHistory {\\n    state\\n    timestamp\\n    numberOfShares {\\n      filled\\n      total\\n      __typename\\n    }\\n    executionPrice\\n    __typename\\n  }\\n  orderKind\\n  __typename\\n}\\n\\nfragment CashTransactionDetailsFragment on BrokerCashTransaction {\\n  cashTransactionType\\n  amount\\n  description\\n  cashTransactionHistory: transactionHistory {\\n    state\\n    timestamp\\n    __typename\\n  }\\n  nonTradeSecurity: security {\\n    ...SecurityNameOnlyFragment\\n    __typename\\n  }\\n  sddiDetails {\\n    fee\\n    grossAmount\\n    __typename\\n  }\\n  taxDetails {\\n    grossAmount\\n    taxAmount\\n    __typename\\n  }\\n  __typename\\n}\\n\\nfragment NonTradeSecurityTransactionDetailsFragment on BrokerNonTradeSecurityTransaction {\\n  isin\\n  nonTradeSecurityTransactionType\\n  quantity\\n  nonTradeAveragePrice: averagePrice\\n  nonTradeSecurityAmount: totalAmount\\n  description\\n  nonTradeSecurityTransactionHistory: transactionHistory {\\n    state\\n    timestamp\\n    __typename\\n  }\\n  nonTradeSecurity: security {\\n    ...SecurityNameOnlyFragment\\n    __typename\\n  }\\n  __typename\\n}\\n\\nfragment EltifTransactionDetailsFragment on BrokerEltifTransaction {\\n  status\\n  side\\n  orderKind\\n  amount\\n  finalisationReason\\n  eltifQuantity\\n  executionPrice\\n  executionDate\\n  earliestSellDate\\n  marketValuation\\n  cancelableDetails {\\n    daysLeft\\n    isCancelable\\n    __typename\\n  }\\n  isMultipleOrdersCancellation\\n  tradingVenue\\n  transactionHistory {\\n    state\\n    amount\\n    eltifQuantity\\n    executionPrice\\n    time {\\n      epochSecond\\n      __typename\\n    }\\n    __typename\\n  }\\n  __typename\\n}"}]'
        )

        resp = requests.post(
            str(self.config.params.url),
            headers=self.config.headers,
            cookies=self.config.cookies,
            data=payload_raw,
        )
        self.raw_data = json.loads(resp.text)
        self.data = self._extract_model_from_json()

    @run_with_duration("save_duration")
    def save(self) -> None:
        file_path = self.get_file_path()
        save_path = file_path.parent
        if not save_path.exists():
            save_path.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as fw:
            json.dump(self.raw_data, fw, indent=2, ensure_ascii=False)

    def stats(self) -> str:
        return f"durations = ( fetch = {self.fetch_duration:.2f}s, save = {self.save_duration:.2f}s )"


class _TransactionsPage:
    page_number: int
    cursor: str
    config: Config
    logger: logging.LoggerAdapter
    data: typing.Optional[TransactionsPageModel]
    raw_data: typing.Optional[typing.Any]
    fetch_duration: float
    save_duration: float

    def __init__(
        self,
        page_number: int,
        cursor: typing.Optional[str],
        config: Config,
        ignore_previous: bool = False,
    ):
        self.page_number = page_number
        self.cursor = "null" if cursor is None else f'"{cursor}"'
        self.config = config
        self.logger = TransactionsPageLoggerAdapter.get_logger(
            logging.getLogger(__name__), page_number
        )
        self.data = None
        self.raw_data = None
        self.fetch_duration = 0.0
        self.save_duration = 0.0

        if not ignore_previous:
            self.__load_cached_data()

    def get_file_path(self) -> pathlib.Path:
        return (
            self.config.params.output_path
            / "transactions"
            / f"page_{self.page_number:03d}.json"
        )

    def __load_cached_data(self) -> None:
        file_path = self.get_file_path()
        if not file_path.exists():
            return
        with open(file_path, "r") as fr:
            self.raw_data = json.load(fr)
            self.data = self._extract_model_from_json()
        self.logger.debug("data loaded from disk")

    def _extract_model_from_json(self) -> TransactionsPageModel:
        if self.raw_data is None:
            raise Exception("no raw_data found for model")
        return TransactionsPageModel.model_validate(
            self.raw_data[0]["data"]["account"]["brokerPortfolio"]["moreTransactions"]
        )

    @run_with_duration("fetch_duration")
    def fetch(self) -> typing.Optional[str]:
        if self.data is not None:
            return None

        payload_raw = (
            '[{"operationName":"moreTransactions","variables":{"personId":"'
            + self.config.params.person_id
            + '","input":{"pageSize":'
            + str(transactions_page_size)
            + ',"type":[],"status":[],"searchTerm":"","cursor":'
            + self.cursor
            + '},"portfolioId":"'
            + self.config.params.portfolio_id
            + '"},"query":"query moreTransactions($personId: ID\u0021, $input: BrokerTransactionInput\u0021, $portfolioId: ID\u0021) {\\n  account(id: $personId) {\\n    id\\n    brokerPortfolio(id: $portfolioId) {\\n      id\\n      moreTransactions(input: $input) {\\n        ...MoreTransactionsFragment\\n        __typename\\n      }\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n\\nfragment MoreTransactionsFragment on BrokerTransactionSummaries {\\n  cursor\\n  total\\n  transactions {\\n    id\\n    currency\\n    type\\n    status\\n    isCancellation\\n    lastEventDateTime\\n    description\\n    ...BrokerCashTransactionSummaryFragment\\n    ...BrokerNonTradeSecurityTransactionSummaryFragment\\n    ...BrokerSecurityTransactionSummaryFragment\\n    ...BrokerEltifTransactionSummaryFragment\\n    __typename\\n  }\\n  __typename\\n}\\n\\nfragment BrokerCashTransactionSummaryFragment on BrokerCashTransactionSummary {\\n  cashTransactionType\\n  amount\\n  relatedIsin\\n  __typename\\n}\\n\\nfragment BrokerNonTradeSecurityTransactionSummaryFragment on BrokerNonTradeSecurityTransactionSummary {\\n  nonTradeSecurityTransactionType\\n  quantity\\n  amount\\n  isin\\n  __typename\\n}\\n\\nfragment BrokerSecurityTransactionSummaryFragment on BrokerSecurityTransactionSummary {\\n  securityTransactionType\\n  quantity\\n  amount\\n  side\\n  isin\\n  __typename\\n}\\n\\nfragment BrokerEltifTransactionSummaryFragment on BrokerEltifTransactionSummary {\\n  amount\\n  eltifQuantity\\n  isin\\n  securityTransactionType\\n  side\\n  __typename\\n}"}]'
        )

        resp = requests.post(
            str(self.config.params.url),
            headers=self.config.headers,
            cookies=self.config.cookies,
            data=payload_raw,
        )
        self.raw_data = json.loads(resp.text)
        self.data = self._extract_model_from_json()

        return self.data.cursor

    @run_with_duration("save_duration")
    def save(self):
        file_path = self.get_file_path()
        save_path = file_path.parent
        if not save_path.exists():
            save_path.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as fw:
            json.dump(self.raw_data, fw, indent=2, ensure_ascii=False)

    def get_transaction_ids(self) -> typing.List[str]:
        if not self.data:
            raise RuntimeError("no fetched data found to get transaction IDs")
        return [txn.id for txn in self.data.transactions]

    def stats(self) -> str:
        return f"durations = ( fetch = {self.fetch_duration:.2f}s, save = {self.save_duration:.2f}s )"


class Orchestrator:
    config: Config
    logger: logging.Logger

    def __init__(self, config: Config) -> None:
        self.config = config
        self.logger = logging.getLogger(__name__)

    def fetch_and_save(self) -> typing.List[str]:
        # transactions information
        page_number: int = -1
        cursor_next: typing.Optional[str] = None

        refetch_transactions_data = True
        while True:
            page_number += 1

            page = _TransactionsPage(
                page_number=page_number,
                cursor=cursor_next,
                config=self.config,
                ignore_previous=refetch_transactions_data,
            )
            try:
                cursor_next = page.fetch()
            except Exception as e:
                self.logger.error(
                    f"error fetching transactions page {page_number}: {e}"
                )
                raise

            if page_number == 0:
                # check if all transactions in the first page, are already in disk.
                # if so, we do not need to refetch anything anymore

                data_not_found = False
                for txn_id in page.get_transaction_ids():
                    transaction = _Transaction(
                        transaction_id=txn_id,
                        config=self.config,
                    )

                    if transaction.data is None:
                        data_not_found = True
                        break

                # if even one of them has empty transaction data, then continue refetch
                refetch_transactions_data = data_not_found

                if not data_not_found:
                    self.logger.info(
                        "no new transactions since last fetch, nothing more to do for this step"
                    )
                    break
                else:
                    # If the first page is different (or no previous file), then changes detected
                    self.logger.debug(
                        "changes detected or no previous transactions data"
                    )
                    transactions_dir = page.get_file_path().parent
                    if transactions_dir.exists():
                        self.logger.debug(
                            f"clearing old transaction files from: {transactions_dir}"
                        )
                        shutil.rmtree(transactions_dir)

            try:
                page.save()
            except Exception as e:
                self.logger.error(f"error saving transactions page {page_number}: {e}")
                raise

            # page stats
            page.logger.info(page.stats())

            if cursor_next is None:
                break

        newly_fetched_ids = []
        # fetch all transaction included in all the pages
        page_number = -1
        while True:
            page_number += 1

            page = _TransactionsPage(
                page_number=page_number,
                cursor=cursor_next,
                config=self.config,
            )
            if page.data is None:
                # since we should have already fetched all the pages, if there is no more data
                # it would mean that there are no pages
                break

            for txn_id in page.get_transaction_ids():
                transaction = _Transaction(
                    transaction_id=txn_id,
                    config=self.config,
                )
                is_new = transaction.data is None
                try:
                    transaction.fetch()
                except Exception as e:
                    self.logger.error(f"error fetching transaction {txn_id}: {e}")
                    raise
                try:
                    transaction.save()
                except Exception as e:
                    self.logger.error(f"error saving transaction {txn_id}: {e}")
                    raise

                # transaction stats
                transaction.logger.info(transaction.stats())
                if is_new:
                    newly_fetched_ids.append(txn_id)

        return newly_fetched_ids

    def get_transactions_details(self) -> typing.Iterator[TransactionDetailModel]:
        page_number = -1
        while True:
            page_number += 1

            page = _TransactionsPage(
                page_number=page_number,
                cursor=None,
                config=self.config,
            )
            if page.data is None:
                # since we should have already fetched all the pages, if there is no more data
                # it would mean that there are no pages
                break

            for txn_id in page.get_transaction_ids():
                transaction = _Transaction(
                    transaction_id=txn_id,
                    config=self.config,
                )
                if transaction.data is None:
                    raise Exception(f"no model data found for transaction {txn_id}")
                yield transaction.data
