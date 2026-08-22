import pytest
from app.voice.schemas import TranscriptResponse
from app.voice.normalizer import VoiceNormalizer
from app.voice.providers import MockSTTProvider
from app.voice.processor import VoiceProcessor

def test_01_normalize_hazaar():
    norm = VoiceNormalizer()
    text = "Rahul se laptop ka price negotiate karo. 42 hazaar target hai."
    res = norm.normalize_monetary_expressions(text)
    assert "42000 target hai." in res

def test_02_normalize_lakh():
    norm = VoiceNormalizer()
    text = "Budget 1.5 lakh hai."
    res = norm.normalize_monetary_expressions(text)
    assert "Budget 150000 hai." in res

def test_03_normalize_crore():
    norm = VoiceNormalizer()
    text = "Project cost 2 crore."
    res = norm.normalize_monetary_expressions(text)
    assert "Project cost 20000000." in res

def test_04_normalize_rupees():
    norm = VoiceNormalizer()
    text = "It should be exactly 50000 rupees."
    res = norm.normalize_monetary_expressions(text)
    assert "exactly ₹50000." in res

def test_05_normalize_rs_prefix():
    norm = VoiceNormalizer()
    text = "Target is Rs 4000."
    res = norm.normalize_monetary_expressions(text)
    assert "Target is ₹4000." in res

def test_06_processor_no_confirmation_needed():
    provider = MockSTTProvider("Call Rahul and negotiate the laptop price.")
    processor = VoiceProcessor(provider)
    res = processor.process_audio(b"audio")
    assert res.requires_confirmation is False
    assert res.confirmation_prompt is None
    assert res.normalized_transcript == "Call Rahul and negotiate the laptop price."

def test_07_processor_confirmation_needed_english():
    provider = MockSTTProvider("My maximum budget is 42000 rupees.")
    processor = VoiceProcessor(provider)
    res = processor.process_audio(b"audio")
    assert res.requires_confirmation is True
    assert "42000" in res.confirmation_prompt
    assert "CONFIRM, EDIT, or CANCEL" in res.confirmation_prompt
    assert "₹42000" in res.normalized_transcript

def test_08_processor_confirmation_needed_hindi():
    # 42000 -> hazaar -> "se upar mat"
    provider = MockSTTProvider("42 hazaar se upar mat jaana.")
    processor = VoiceProcessor(provider)
    res = processor.process_audio(b"audio")
    assert res.requires_confirmation is True
    assert "42000" in res.confirmation_prompt
    assert "42000 se upar mat jaana" in res.normalized_transcript

def test_09_processor_missing_number():
    provider = MockSTTProvider("Do not go over the maximum limit.")
    processor = VoiceProcessor(provider)
    res = processor.process_audio(b"audio")
    assert res.requires_confirmation is True
    assert "couldn't understand the exact number" in res.confirmation_prompt
