import pytest
from app.evaluation.failure_injector import FailureInjector, FailureType

def test_failure_injection_and_consumption():
    injector = FailureInjector()
    
    # Inject a failure
    injector.inject(FailureType.PRIVACY_LEAK)
    assert FailureType.PRIVACY_LEAK in injector.active_failures
    
    # Check and consume it
    should_fail = injector.check_and_consume(FailureType.PRIVACY_LEAK)
    assert should_fail is True
    
    # Check again - should be consumed and allow recovery
    should_fail_again = injector.check_and_consume(FailureType.PRIVACY_LEAK)
    assert should_fail_again is False

def test_failure_logging():
    injector = FailureInjector()
    
    injector.log_failure(
        failure_type=FailureType.INVALID_AI_OUTPUT,
        what_happened="AI returned unparseable text",
        recovery="Fallback parser invoked",
        result="Negotiation continued"
    )
    
    assert len(injector.logs) == 1
    log = injector.logs[0].to_dict()
    assert log["failure_type"] == "INVALID_AI_OUTPUT"
    assert log["recovery"] == "Fallback parser invoked"
