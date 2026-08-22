import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text, Float, JSON
from sqlalchemy.orm import relationship
from app.database.core import Base

class VisibilityEnum(str, enum.Enum):
    PRIVATE = "PRIVATE"
    SHARED = "SHARED"
    SYSTEM = "SYSTEM"

class ConstraintTypeEnum(str, enum.Enum):
    HARD = "HARD"
    SOFT = "SOFT"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    missions = relationship("Mission", back_populates="user")
    agents = relationship("Agent", back_populates="user")

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="agents")
    negotiations = relationship("Negotiation", back_populates="agent")

class Mission(Base):
    __tablename__ = "missions"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    goal_description = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="missions")
    constraints = relationship("Constraint", back_populates="mission")
    permissions = relationship("Permission", back_populates="mission")
    negotiations = relationship("Negotiation", back_populates="mission")

class Constraint(Base):
    __tablename__ = "constraints"
    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"))
    key = Column(String) # e.g., 'max_price'
    operator = Column(String) # e.g., '<='
    value = Column(String) # Stored as string, interpreted later
    visibility = Column(Enum(VisibilityEnum), default=VisibilityEnum.PRIVATE)
    type = Column(Enum(ConstraintTypeEnum), default=ConstraintTypeEnum.HARD)
    
    mission = relationship("Mission", back_populates="constraints")

class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"))
    action_type = Column(String)
    is_allowed = Column(Boolean, default=False)
    
    mission = relationship("Mission", back_populates="permissions")

class CommunicationSession(Base):
    __tablename__ = "communication_sessions"
    id = Column(Integer, primary_key=True, index=True)
    session_protocol = Column(String) # e.g., 'websocket', 'webrtc'
    connection_string = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    negotiation = relationship("Negotiation", back_populates="session", uselist=False)

class Negotiation(Base):
    __tablename__ = "negotiations"
    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"))
    agent_id = Column(Integer, ForeignKey("agents.id"))
    session_id = Column(Integer, ForeignKey("communication_sessions.id"))
    status = Column(String, default="PROPOSING") # e.g., PROPOSING, COUNTERING, AGREED, WALK_AWAY
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    mission = relationship("Mission", back_populates="negotiations")
    agent = relationship("Agent", back_populates="negotiations")
    session = relationship("CommunicationSession", back_populates="negotiation")
    turns = relationship("NegotiationTurn", back_populates="negotiation")
    agreement = relationship("Agreement", back_populates="negotiation", uselist=False)
    memories = relationship("Memory", back_populates="negotiation")
    audit_events = relationship("AuditEvent", back_populates="negotiation")

class NegotiationTurn(Base):
    __tablename__ = "negotiation_turns"
    id = Column(Integer, primary_key=True, index=True)
    negotiation_id = Column(Integer, ForeignKey("negotiations.id"))
    turn_number = Column(Integer)
    sender = Column(String) # e.g., 'AGENT', 'COUNTERPARTY'
    raw_message = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    negotiation = relationship("Negotiation", back_populates="turns")
    offer = relationship("Offer", back_populates="turn", uselist=False)

class Offer(Base):
    __tablename__ = "offers"
    id = Column(Integer, primary_key=True, index=True)
    turn_id = Column(Integer, ForeignKey("negotiation_turns.id"))
    structured_data = Column(JSON) # e.g., {"price": 4500, "projector": true}
    
    turn = relationship("NegotiationTurn", back_populates="offer")

class Agreement(Base):
    __tablename__ = "agreements"
    id = Column(Integer, primary_key=True, index=True)
    negotiation_id = Column(Integer, ForeignKey("negotiations.id"))
    agreed_terms = Column(JSON)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    negotiation = relationship("Negotiation", back_populates="agreement")

class MemoryTypeEnum(str, enum.Enum):
    USER_PREFERENCE = "USER_PREFERENCE"
    NEGOTIATION_HISTORY = "NEGOTIATION_HISTORY"
    CONTACT_CONTEXT = "CONTACT_CONTEXT"
    AGREEMENT = "AGREEMENT"
    FOLLOW_UP = "FOLLOW_UP"
    FACT = "FACT"
    INFERENCE = "INFERENCE"
    TEMPORARY_CONTEXT = "TEMPORARY_CONTEXT"

class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    negotiation_id = Column(Integer, ForeignKey("negotiations.id"), nullable=True)
    
    type = Column(Enum(MemoryTypeEnum), default=MemoryTypeEnum.FACT)
    content = Column(Text)
    source = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    confidence = Column(Float, default=1.0)
    privacy = Column(Enum(VisibilityEnum), default=VisibilityEnum.PRIVATE)
    expiration = Column(DateTime, nullable=True)
    
    user = relationship("User", backref="memories")
    negotiation = relationship("Negotiation", back_populates="memories")

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True, index=True)
    negotiation_id = Column(Integer, ForeignKey("negotiations.id"), nullable=True)
    event_type = Column(String) # e.g., 'CONSTRAINT_VIOLATION_BLOCKED', 'MISSION_ACTIVATED'
    description = Column(Text)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    negotiation = relationship("Negotiation", back_populates="audit_events")

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"))
    test_scenario = Column(String)
    success = Column(Boolean)
    metrics = Column(JSON) # e.g., {"turns": 4, "constraint_breached": false}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
