class FakeChannel:
    """A deterministic mock channel for testing."""
    def __init__(self):
        self.sent_messages = []
        self.queue_to_receive = []

    def send(self, message: str):
        self.sent_messages.append(message)

    def receive(self) -> str:
        if self.queue_to_receive:
            return self.queue_to_receive.pop(0)
        return None
        
    def inject_incoming(self, message: str):
        """Used by tests to mock the counterparty speaking."""
        self.queue_to_receive.append(message)
