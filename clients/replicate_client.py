from clients.base_client import Client


class ReplicateClient(Client):
    def __init__(self, api_key):
        super().__init__(api_key)