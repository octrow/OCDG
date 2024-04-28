# commit.py
import os
import json
import re
import traceback
from sys import stdout

class Commit:
    def __init__(self, hash, author, date, message, repo):
        self.hash = hash
        self.author = author
        self.date = date
        self.message = message
        self.repo = repo

    def process_commit(self, db, client):
        # Format the filename using commit date and hash
        filename = f"{commit_diff_dir}/{self.date}_{self.hash}.diff"
        print(f"Filename: {filename}")

        try:
            diff_content = self.repo.get_diff(self.hash)
        except Exception as e:
            print(f"Error executing git diff: {e}")
            return  # Skip this commit

        # Write commit info and diff to the separate file
        self.write_commit_info_to_file(filename, diff_content)

        # Generate new commit message
        status = True
        try:
            new_commit_message = self.generate_new_commit_message(diff_content, client)
            print(f"New commit message: {new_commit_message}...")
            # Save the new commit message
            new_message_filename = f"{commit_diff_dir}/{self.date}_{self.hash}_new_message.txt"
            with open(new_message_filename, 'w') as file:
                file.write(str(new_commit_message))
        except Exception as e:
            print(f"Exception: {traceback.format_exc()} {str(e)}")
            status = False
        finally:
            self.update_commit_descriptions(status)  # Update descriptions regardless of success or error
            if not status:
                raise Exception("Failed to generate new commit message")
            db.update_commit_status(self.hash, True)

    # ... rest of the methods from the original code go here ...
