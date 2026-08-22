import pytest
from app.voice.normalizer import VoiceNormalizer

def test_normalize_time_expressions():
    norm = VoiceNormalizer()
    text = "Rahul ko kal shaam 6 baje call karna."
    result = norm.normalize_time_expressions(text)
    
    assert "tomorrow" in result
    assert "evening" in result
    assert "kal" not in result
    assert "shaam" not in result

def test_normalize_ambiguity():
    norm = VoiceNormalizer()
    
    # Unambiguous
    _, is_ambig1 = norm.process("42 hazaar se upar mat jaana")
    assert not is_ambig1
    
    # Ambiguous Hindi phrase "lagbhag" (approximately)
    _, is_ambig2 = norm.process("Lagbhag 40 hazaar chalega")
    assert is_ambig2
    
    # Ambiguous Past/Future tense confusion
    _, is_ambig3 = norm.process("Kal usne bola tha")
    assert is_ambig3

def test_normalize_monetary_combinations():
    norm = VoiceNormalizer()
    text = "1.25 lakh is too much, try 80 hazaar."
    result = norm.normalize_monetary_expressions(text)
    
    assert "125000" in result
    assert "80000" in result
