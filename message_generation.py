class MessageGenerator:
    def __init__(self, client):
        self.client = client

    def generate_commit_message(self, diff, old_message):
        # Construct prompt using diff and old message
        prompt = f"... (Your prompt template here) ..."

        # Generate new message using the client
        new_message = self.client.generate_text(prompt, max_tokens=2000)
        return new_message