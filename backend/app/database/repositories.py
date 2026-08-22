from sqlalchemy.orm import Session
from app.database import models

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, username: str):
    user = models.User(username=username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_mission(db: Session, user_id: int, title: str, goal_description: str):
    mission = models.Mission(user_id=user_id, title=title, goal_description=goal_description)
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return mission

def create_constraint(db: Session, mission_id: int, key: str, operator: str, value: str, visibility: models.VisibilityEnum, c_type: models.ConstraintTypeEnum):
    constraint = models.Constraint(
        mission_id=mission_id, 
        key=key, 
        operator=operator, 
        value=value,
        visibility=visibility,
        type=c_type
    )
    db.add(constraint)
    db.commit()
    db.refresh(constraint)
    return constraint

def log_audit_event(db: Session, event_type: str, description: str, negotiation_id: int = None):
    event = models.AuditEvent(
        event_type=event_type,
        description=description,
        negotiation_id=negotiation_id
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
