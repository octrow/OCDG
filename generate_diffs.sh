#!/bin/bash

# Create directory for commit diffs
mkdir -p commit_diff

# Extract commit information and loop over each commit
git log --pretty=format:'%h,%an,%ad,%s' --date=format:%Y-%m-%d | while IFS=, read -r hash author date message
do
    # Format the filename using commit date and hash
    filename="commit_diff/${date}_${hash}.diff"

    # Write commit info and diff to the separate file
    echo "Commit: $hash" > "$filename"
    echo "Author: $author" >> "$filename"
    echo "Date: $date" >> "$filename"
    echo "Message: $message" >> "$filename"
    echo "Diff:" >> "$filename"
    git diff "$hash^!" >> "$filename"
done
