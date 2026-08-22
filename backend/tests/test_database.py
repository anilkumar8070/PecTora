import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.core import Base
from app.database import models, repositories

# Use memory database for tests
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_create_user(db):
    user = repositories.create_user(db, "test_user")
    assert user.id is not None
    assert user.username == "test_user"

def test_create_mission_with_constraints(db):
    user = repositories.create_user(db, "test_user")
    mission = repositories.create_mission(db, user.id, "Test Mission", "Goal description")
    
    constraint_private_hard = repositories.create_constraint(
        db, mission.id, "budget", "<=", "100", 
        models.VisibilityEnum.PRIVATE, models.ConstraintTypeEnum.HARD
    )
    
    assert constraint_private_hard.visibility == models.VisibilityEnum.PRIVATE
    assert constraint_private_hard.type == models.ConstraintTypeEnum.HARD

def test_audit_log(db):
    event = repositories.log_audit_event(db, "TEST_EVENT", "Test description")
    assert event.id is not None
    assert event.event_type == "TEST_EVENT"
