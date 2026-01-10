#!/bin/bash

# eg: export DATA_DIR=./raw_data/data_points; ./scripts/scalable/field_exists.sh

field_name=".data.account.brokerPortfolio.transactionDetails.finalisationReason"

find "$DATA_DIR" -name "*.json" -print0 | while IFS= read -r -d $'\0' file; do
  if jq -e "((.[]? // .) |  $field_name) | select(. != null)" "$file" >/dev/null; then
    echo "File: $file has a non-null 'fee' value."
  fi
done