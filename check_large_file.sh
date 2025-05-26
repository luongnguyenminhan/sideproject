#!/bin/bash

# check_large_file.sh - Find Python files with more than N lines

# Check if argument is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <max_line_count>"
    echo "Example: $0 500"
    exit 1
fi

# Get the maximum line count from command line argument
MAX_LINES=$1

# Ensure the argument is a positive integer
if ! [[ "$MAX_LINES" =~ ^[0-9]+$ ]]; then
    echo "Error: Please provide a positive integer for the maximum line count."
    exit 1
fi

echo "Checking for Python files with more than $MAX_LINES lines in ./app directory..."

# Find all Python files in the ./app directory and check line count
find ./app -type f -name "*.py" | while read file; do
    # Count the number of lines in the file
    line_count=$(wc -l < "$file")
    
    # Check if line count exceeds the maximum
    if [ "$line_count" -gt "$MAX_LINES" ]; then
        echo "$file: $line_count lines"
    fi
done

echo "Scan complete."