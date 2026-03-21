#!/bin/bash

# eg: export DATA_DIR=./raw_data/data_points; ./scripts/scalable/unique_values.sh

field_name=".data.account.brokerPortfolio.transactionDetails.side"

# Declare an associative array to store the first file for each type
declare -A first_occurrence

# Use process substitution (< <(...)) to run the while loop in the current shell.
# This ensures that modifications to 'first_occurrence' persist after the loop.
while IFS= read -r -d $'\0' file; do
  # Extract the type. '// empty' ensures that if the type is null or not found, jq outputs nothing.
  type=$(jq -r "((.[]? // .) | $field_name // empty)" "$file")
  
  # If a type was extracted and it's not already in our associative array, store it
  if [[ -n "$type" && ! -v "first_occurrence[$type]" ]]; then
    first_occurrence["$type"]="$file"
  fi
done < <(find "$DATA_DIR" -name "*.json" -print0) # The output of find is fed into the while loop

for type in "${!first_occurrence[@]}"; do
  echo "Type: $type, First found in: ${first_occurrence[$type]}"
done | sort