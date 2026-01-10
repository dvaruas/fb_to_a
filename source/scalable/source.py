import json
import logging
import os
import shutil
from typing import Optional

import requests

from source.scalable.config import SourceScalableCapitalConfig
from utils.with_duration import run_with_duration

transactions_page_size = 200

_module_logger = logging.getLogger(__name__)


class SourceScalableCapital:
    def __init__(self, config: SourceScalableCapitalConfig):
        self.config = config
        self.logger = _module_logger

    def fetch_and_save(self):
        # transactions information
        page_number = -1
        cursor_next: Optional[str] = None

        while True:
            page_number += 1

            page = ScalableCapitalSecuritiesTransactionsPage(
                page_number=page_number,
                cursor=cursor_next,
                config=self.config,
                ignore_previous=True if page_number == 0 else False,
            )
            try:
                cursor_next = page.fetch()
            except Exception as e:
                self.logger.error(
                    f"error fetching transactions page {page_number}: {e}"
                )
                raise

            if page_number == 0:
                # for the first page, do a diff check to see if there have been any new transactions since last fetch
                has_diff = page.has_diff_with_previous()
                if not has_diff:
                    self.logger.info(
                        "no new transactions since last fetch, nothing more to do for this step"
                    )
                    break
                else:
                    # If the first page is different (or no previous file), then changes detected
                    self.logger.info("changes detected or no previous data")
                    transactions_dir = os.path.dirname(page.file_path)
                    if os.path.exists(transactions_dir):
                        self.logger.info(
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

            if cursor_next == None:
                break

        # fetch all transaction included in all the pages
        page_number = -1
        while True:
            page_number += 1

            page = ScalableCapitalSecuritiesTransactionsPage(
                page_number=page_number,
                cursor=cursor_next,
                config=self.config,
            )
            if page.fetch_response == None:
                break

            for transaction_id in page.get_transaction_ids():
                transaction = ScalableCapitalSecuritiesTransaction(
                    transaction_id=transaction_id,
                    config=self.config,
                )
                try:
                    transaction.fetch()
                except Exception as e:
                    self.logger.error(
                        f"error fetching transaction {transaction_id}: {e}"
                    )
                    raise
                try:
                    transaction.save()
                except Exception as e:
                    self.logger.error(f"error saving transaction {transaction_id}: {e}")
                    raise

                # transaction stats
                transaction.logger.info(transaction.stats())


class ScalableCapitalSecuritiesTransactionsPageLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return f"[transactions {self.extra['page_no']}] {msg}", kwargs


class ScalableCapitalSecuritiesTransactionsPage:
    def __init__(
        self,
        page_number: int,
        cursor: Optional[str],
        config: SourceScalableCapitalConfig,
        ignore_previous: bool = False,
    ):
        self.page_number = page_number
        self.cursor = "null" if cursor == None else f'"{cursor}"'
        self.file_name = f"page_{page_number:03d}.json"
        save_path = os.path.join(config.output_path, "transactions")
        self.file_path = os.path.join(save_path, self.file_name)
        self.config = config
        self.logger = ScalableCapitalSecuritiesTransactionsPageLoggerAdapter(
            _module_logger, {"page_no": page_number}
        )

        self.fetch_response = None
        if not ignore_previous and os.path.exists(self.file_path):
            with open(self.file_path, "r") as fr:
                self.fetch_response = json.load(fr)
            self.logger.info("data loaded from disk")

        self.fetch_duration = 0.0
        self.save_duration = 0.0

    @run_with_duration("fetch_duration")
    def fetch(self) -> Optional[str]:
        if self.fetch_response != None:
            return None

        payload_raw = (
            '[{"operationName":"moreTransactions","variables":{"personId":"'
            + self.config.person_id
            + '","input":{"pageSize":'
            + str(transactions_page_size)
            + ',"type":[],"status":[],"searchTerm":"","cursor":'
            + self.cursor
            + '},"portfolioId":"'
            + self.config.portfolio_id
            + '"},"query":"query moreTransactions($personId: ID\u0021, $input: BrokerTransactionInput\u0021, $portfolioId: ID\u0021) {\\n  account(id: $personId) {\\n    id\\n    brokerPortfolio(id: $portfolioId) {\\n      id\\n      moreTransactions(input: $input) {\\n        ...MoreTransactionsFragment\\n        __typename\\n      }\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n\\nfragment MoreTransactionsFragment on BrokerTransactionSummaries {\\n  cursor\\n  total\\n  transactions {\\n    id\\n    currency\\n    type\\n    status\\n    isCancellation\\n    lastEventDateTime\\n    description\\n    ...BrokerCashTransactionSummaryFragment\\n    ...BrokerNonTradeSecurityTransactionSummaryFragment\\n    ...BrokerSecurityTransactionSummaryFragment\\n    ...BrokerEltifTransactionSummaryFragment\\n    __typename\\n  }\\n  __typename\\n}\\n\\nfragment BrokerCashTransactionSummaryFragment on BrokerCashTransactionSummary {\\n  cashTransactionType\\n  amount\\n  relatedIsin\\n  __typename\\n}\\n\\nfragment BrokerNonTradeSecurityTransactionSummaryFragment on BrokerNonTradeSecurityTransactionSummary {\\n  nonTradeSecurityTransactionType\\n  quantity\\n  amount\\n  isin\\n  __typename\\n}\\n\\nfragment BrokerSecurityTransactionSummaryFragment on BrokerSecurityTransactionSummary {\\n  securityTransactionType\\n  quantity\\n  amount\\n  side\\n  isin\\n  __typename\\n}\\n\\nfragment BrokerEltifTransactionSummaryFragment on BrokerEltifTransactionSummary {\\n  amount\\n  eltifQuantity\\n  isin\\n  securityTransactionType\\n  side\\n  __typename\\n}"}]'
        )

        resp = requests.post(
            self.config.url,
            headers=self.config.headers,
            cookies=self.config.cookies,
            data=payload_raw,
        )
        self.fetch_response = json.loads(resp.text)

        cursor = self.fetch_response[0]["data"]["account"]["brokerPortfolio"][
            "moreTransactions"
        ]["cursor"]

        return cursor

    @run_with_duration("save_duration")
    def save(self):
        save_path = os.path.dirname(self.file_path)
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        with open(self.file_path, "w", encoding="utf-8") as fw:
            json.dump(self.fetch_response, fw, indent=2, ensure_ascii=False)

    def get_transaction_ids(self):
        if not self.fetch_response:
            raise RuntimeError("no fetched data found to get transaction IDs")

        transactions = self.fetch_response[0]["data"]["account"]["brokerPortfolio"][
            "moreTransactions"
        ]["transactions"]
        return [txn["id"] for txn in transactions]

    def has_diff_with_previous(self) -> bool:
        if not self.fetch_response:
            raise RuntimeError("no fetched data found for diff comparison")

        if not os.path.exists(self.file_path):
            return True

        with open(self.file_path, "r") as fr:
            previous_data = json.load(fr)

        return self.fetch_response != previous_data

    def stats(self):
        return f"durations = ( fetch = {self.fetch_duration:.2f}s, save = {self.save_duration:.2f}s )"


class TransactionLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return f"[txn {self.extra['transaction_id']}] {msg}", kwargs


class ScalableCapitalSecuritiesTransaction:
    def __init__(
        self,
        transaction_id: str,
        config: SourceScalableCapitalConfig,
        ignore_previous: bool = False,
    ):
        self.transaction_id = transaction_id
        self.file_name = f"txn_{transaction_id}.json"
        save_path = os.path.join(config.output_path, "data_points")
        self.file_path = os.path.join(save_path, self.file_name)
        self.config = config

        display_id = transaction_id
        if len(transaction_id) > 13:
            display_id = f"{transaction_id[:10]}...{transaction_id[-3:]}"

        self.logger = TransactionLoggerAdapter(
            _module_logger, {"transaction_id": display_id}
        )

        self.fetch_response = None
        if not ignore_previous and os.path.exists(self.file_path):
            with open(self.file_path, "r") as fr:
                self.fetch_response = json.load(fr)
            self.logger.info("data loaded from disk")

        self.fetch_duration = 0.0
        self.save_duration = 0.0

    @run_with_duration("fetch_duration")
    def fetch(self) -> None:
        if self.fetch_response != None:
            return

        payload_raw = (
            '[{"operationName":"getTransactionDetails","variables":{"personId":"'
            + self.config.person_id
            + '","transactionId":"'
            + self.transaction_id
            + '","portfolioId":"'
            + self.config.portfolio_id
            + '"},"query":"query getTransactionDetails($personId: ID\u0021, $transactionId: ID\u0021, $portfolioId: ID\u0021) {\\n  account(id: $personId) {\\n    id\\n    brokerPortfolio(id: $portfolioId) {\\n      id\\n      transactionDetails(id: $transactionId) {\\n        ...TransactionDetailsFragment\\n        __typename\\n      }\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n\\nfragment TransactionDetailsFragment on BrokerTransaction {\\n  id\\n  currency\\n  type\\n  documents {\\n    id\\n    url\\n    label\\n    __typename\\n  }\\n  lastEventDateTime\\n  isPending\\n  isCancellation\\n  security {\\n    ...SecurityNameOnlyFragment\\n    __typename\\n  }\\n  transactionReference\\n  ...SecurityTransactionDetailsFragment\\n  ...CashTransactionDetailsFragment\\n  ...NonTradeSecurityTransactionDetailsFragment\\n  ...EltifTransactionDetailsFragment\\n  __typename\\n}\\n\\nfragment SecurityNameOnlyFragment on Security {\\n  id\\n  name\\n  isin\\n  __typename\\n}\\n\\nfragment SecurityTransactionDetailsFragment on BrokerSecurityTransaction {\\n  id\\n  side\\n  status\\n  numberOfShares {\\n    filled\\n    total\\n    __typename\\n  }\\n  averagePrice\\n  totalAmount\\n  finalisationReason\\n  limitPrice\\n  stopPrice\\n  validUntil\\n  isCancellationRequested\\n  tradeTransactionAmounts {\\n    marketValuation\\n    taxAmount\\n    transactionFee\\n    venueFee\\n    cryptoSpreadFee\\n    __typename\\n  }\\n  tradingVenue\\n  fee\\n  transactionalFee\\n  taxes\\n  securityTransactionHistory: transactionHistory {\\n    state\\n    timestamp\\n    numberOfShares {\\n      filled\\n      total\\n      __typename\\n    }\\n    executionPrice\\n    __typename\\n  }\\n  orderKind\\n  __typename\\n}\\n\\nfragment CashTransactionDetailsFragment on BrokerCashTransaction {\\n  cashTransactionType\\n  amount\\n  description\\n  cashTransactionHistory: transactionHistory {\\n    state\\n    timestamp\\n    __typename\\n  }\\n  nonTradeSecurity: security {\\n    ...SecurityNameOnlyFragment\\n    __typename\\n  }\\n  sddiDetails {\\n    fee\\n    grossAmount\\n    __typename\\n  }\\n  taxDetails {\\n    grossAmount\\n    taxAmount\\n    __typename\\n  }\\n  __typename\\n}\\n\\nfragment NonTradeSecurityTransactionDetailsFragment on BrokerNonTradeSecurityTransaction {\\n  isin\\n  nonTradeSecurityTransactionType\\n  quantity\\n  nonTradeAveragePrice: averagePrice\\n  nonTradeSecurityAmount: totalAmount\\n  description\\n  nonTradeSecurityTransactionHistory: transactionHistory {\\n    state\\n    timestamp\\n    __typename\\n  }\\n  nonTradeSecurity: security {\\n    ...SecurityNameOnlyFragment\\n    __typename\\n  }\\n  __typename\\n}\\n\\nfragment EltifTransactionDetailsFragment on BrokerEltifTransaction {\\n  status\\n  side\\n  orderKind\\n  amount\\n  finalisationReason\\n  eltifQuantity\\n  executionPrice\\n  executionDate\\n  earliestSellDate\\n  marketValuation\\n  cancelableDetails {\\n    daysLeft\\n    isCancelable\\n    __typename\\n  }\\n  isMultipleOrdersCancellation\\n  tradingVenue\\n  transactionHistory {\\n    state\\n    amount\\n    eltifQuantity\\n    executionPrice\\n    time {\\n      epochSecond\\n      __typename\\n    }\\n    __typename\\n  }\\n  __typename\\n}"}]'
        )

        resp = requests.post(
            self.config.url,
            headers=self.config.headers,
            cookies=self.config.cookies,
            data=payload_raw,
        )
        self.fetch_response = json.loads(resp.text)

    @run_with_duration("save_duration")
    def save(self):
        save_path = os.path.dirname(self.file_path)
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        with open(self.file_path, "w", encoding="utf-8") as fw:
            json.dump(self.fetch_response, fw, indent=2, ensure_ascii=False)

    def stats(self):
        return f"durations = ( fetch = {self.fetch_duration:.2f}s, save = {self.save_duration:.2f}s )"
