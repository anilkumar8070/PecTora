import pytest
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.core import Base
from app.database.models import User, MemoryTypeEnum
from app.memory.engine import MemoryEngine

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    # Create test user
    u = User(username="testuser")
    session.add(u)
    session.commit()
    
    yield session
    session.close()

def test_add_memory(db_session):
    engine = MemoryEngine(db_session)
    mem = engine.add_memory(
        user_id=1,
        content="I prefer Fridays.",
        type=MemoryTypeEnum.USER_PREFERENCE,
        source="EXPLICIT_USER_STATEMENT"
    )
    
    assert mem.id is not None
    assert mem.content == "I prefer Fridays."

def test_retrieval_relevance(db_session):
    engine = MemoryEngine(db_session)
    engine.add_memory(1, "I love apples", MemoryTypeEnum.FACT, "EXPLICIT")
    engine.add_memory(1, "I hate bananas", MemoryTypeEnum.FACT, "EXPLICIT")
    
    results = engine.retrieve_relevant(1, "apples")
    assert len(results) == 1
    assert "apples" in results[0].content

def test_contradiction_explicit_wins_over_inference(db_session):
    engine = MemoryEngine(db_session)
    
    # AI inferred that the user likes Fridays based on chat history
    engine.add_memory(
        1, 
        "User prefers Friday.", 
        MemoryTypeEnum.INFERENCE, 
        "INFERRED"
    )
    
    time.sleep(0.1) # ensure timestamp difference
    
    # User explicitly states otherwise later
    engine.add_memory(
        1, 
        "I don't care about Friday anymore.", 
        MemoryTypeEnum.USER_PREFERENCE, 
        "EXPLICIT_USER_STATEMENT"
    )
    
    results = engine.retrieve_relevant(1, "Friday")
    
    assert len(results) == 1
    assert "don't care about Friday" in results[0].content
    assert results[0].source == "EXPLICIT_USER_STATEMENT"

def test_contradiction_newer_explicit_wins_over_older_explicit(db_session):
    engine = MemoryEngine(db_session)
    
    engine.add_memory(
        1, 
        "I always want a warranty.", 
        MemoryTypeEnum.USER_PREFERENCE, 
        "EXPLICIT_USER_STATEMENT"
    )
    
    time.sleep(0.1)
    
    engine.add_memory(
        1, 
        "Actually, warranty is not needed.", 
        MemoryTypeEnum.USER_PREFERENCE, 
        "EXPLICIT_USER_STATEMENT"
    )
    
    results = engine.retrieve_relevant(1, "warranty")
    
    assert len(results) == 1
    assert "not needed" in results[0].content
