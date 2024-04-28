import os
import sqlite3
import time

# Create directory for commit diffs
commit_diff_dir = "commit_diff"
os.makedirs(commit_diff_dir, exist_ok=True)
print(f"Created directory: {commit_diff_dir}")

# Create a SQLite3 database and table for storing commit information
conn = sqlite3.connect('commits.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS commits
             (hash text PRIMARY KEY, author text, date text, message text, status boolean)''')
print("Created commits table")


def update_commit_status(hash, status):
    c.execute("UPDATE commits SET status = ? WHERE hash = ?", (status, hash))
    conn.commit()


def write_commit_info_to_file(filename, hash, author, date, message, diff_content):
    with open(filename, 'w') as file:
        file.write(f"Commit: {hash}\n")
        file.write(f"Author: {author}\n")
        file.write(f"Date: {date}\n")
        file.write(f"Message: {message}\n")
        file.write('Diff:\n')
        file.write(diff_content)

# Extract commit information and loop over each commit
commits = os.popen("git log --pretty=format:'%h,%an,%ad,%s' --date=format:%Y-%m-%d").read().strip().split('\n')
print(f"Extracted {len(commits)} commits")
for commit_info in commits:
    print(f"Processing commit: {commit_info}")
    hash, author, date, message = commit_info.split(',', maxsplit=3)
    print(f"Commit: {hash}, Author: {author}, Date: {date}, Message: {message}")
    # Format the filename using commit date and hash
    filename = f"{commit_diff_dir}/{date}_{hash}.diff"
    print(f"Filename: {filename}")
    try:
        diff_content = os.popen(f"git diff {hash}^!").read()
    except Exception as e:
        print(f"Error executing git diff: {e}")
        continue # Skip this commit
    # Write commit info and diff to the separate file
    write_commit_info_to_file(filename, hash, author, date, message, diff_content)

    # Update the status of the commit in the SQLite3 table
    update_commit_status(hash, True)
