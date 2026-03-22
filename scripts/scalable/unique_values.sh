#!/bin/bash

# eg: export DATA_DIR=./raw_data/data_points; ./scripts/scalable/unique_values.sh

DEFAULT_DATA_DIR="./data/raw_data/data_points"
DATA_DIR="${DATA_DIR:-$DEFAULT_DATA_DIR}"

field_name=".data.account.brokerPortfolio.transactionDetails.status"

# Split the field_name to check if the exact key exists rather than having null for both missing and explicit null
parent_path="${field_name%.*}"
if [[ -z "$parent_path" || "$parent_path" == "$field_name" ]]; then
  parent_path="."
fi
leaf_key="${field_name##*.}"

# Declare an associative array to store the first file for each type
declare -A first_occurrence

# Use process substitution (< <(...)) to run the while loop in the current shell.
# This ensures that modifications to 'first_occurrence' persist after the loop.
while IFS= read -r -d $'\0' file; do
  # Extract the type. If the field is missing, output <MISSING>.
  type=$(jq -r "((.[]? // .) | if ($parent_path | type) == \"object\" and ($parent_path | has(\"$leaf_key\")) then $field_name else \"<MISSING>\" end)" "$file")
  
  # If a type was extracted and it's not already in our associative array, store it
  if [[ -n "$type" && ! -v "first_occurrence[$type]" ]]; then
    first_occurrence["$type"]="$file"
  fi
done < <(find "$DATA_DIR" -name "*.json" -print0) # The output of find is fed into the while loop

for type in "${!first_occurrence[@]}"; do
  echo "Type: $type, First found in: ${first_occurrence[$type]}"
done | sort