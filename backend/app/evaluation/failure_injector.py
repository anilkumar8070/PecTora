import enum
from typing import List, Dict, Any
from datetime import datetime, timezone

class FailureType(str, enum.Enum):
    AI_TIMEOUT = "AI_TIMEOUT"
    INVALID_AI_OUTPUT = "INVALID_AI_OUTPUT"
    WEBSOCKET_DISCONNECT = "WEBSOCKET_DISCONNECT"
    HUMAN_DISCONNECT = "HUMAN_DISCONNECT"
    CONTRADICTORY_OFFER = "CONTRADICTORY_OFFER"
    REPEATED_OFFER = "REPEATED_OFFER"
    IMPOSSIBLE_CONSTRAINT = "IMPOSSIBLE_CONSTRAINT"
    MISSING_INFO = "MISSING_INFO"
    VERIFICATION_FAILURE = "VERIFICATION_FAILURE"
    PRIVACY_LEAK = "PRIVACY_LEAK"

class FailureLogEntry:
    def __init__(self, failure_type: FailureType, what_happened: str, recovery: str, result: str):
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.failure_type = failure_type
        self.what_happened = what_happened
        self.recovery = recovery
        self.result = result
        
    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "failure_type": self.failure_type.value,
            "what_happened": self.what_happened,
            "recovery": self.recovery,
            "result": self.result
        }

class FailureInjector:
    """
    Controlled framework to intentionally inject faults into the Pectora architecture
    to demonstrate and evaluate the system's recovery mechanisms.
    """
    def __init__(self):
        self.active_failures: List[FailureType] = []
        self.logs: List[FailureLogEntry] = []
        
    def inject(self, failure_type: FailureType):
        if failure_type not in self.active_failures:
            self.active_failures.append(failure_type)
            
    def clear(self, failure_type: FailureType):
        if failure_type in self.active_failures:
            self.active_failures.remove(failure_type)
            
    def log_failure(self, failure_type: FailureType, what_happened: str, recovery: str, result: str):
        entry = FailureLogEntry(failure_type, what_happened, recovery, result)
        self.logs.append(entry)
        
    def check_and_consume(self, failure_type: FailureType) -> bool:
        """Returns True if the failure is active, and removes it so the system can recover on the next retry."""
        if failure_type in self.active_failures:
            self.active_failures.remove(failure_type)
            return True
        return False

# Global instance for testing/demo
injector = FailureInjector()
