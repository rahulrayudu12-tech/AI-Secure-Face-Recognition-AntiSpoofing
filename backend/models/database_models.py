from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, LargeBinary, Text
from sqlalchemy.orm import relationship
from backend.database.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(20), default="user") # "admin" or "user"
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    templates = relationship("FaceTemplate", back_populates="user", cascade="all, delete-orphan")
    auth_logs = relationship("AuthenticationLog", back_populates="user")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "has_face_enrolled": len(self.templates) > 0,
            "enrolled_templates_count": len(self.templates)
        }

class FaceTemplate(Base):
    __tablename__ = "face_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    embedding = Column(LargeBinary, nullable=False) # Serialized 512-D float32 numpy array
    angle = Column(String(20), default="frontal")   # frontal, left, right
    quality_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="templates")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "angle": self.angle,
            "quality_score": round(self.quality_score, 4) if self.quality_score else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class AuthenticationLog(Base):
    __tablename__ = "authentication_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    identity_score = Column(Float, default=0.0)
    liveness_score = Column(Float, default=0.0)
    decision = Column(String(50), nullable=False) # ACCESS_GRANTED, ACCESS_DENIED, SPOOF_DETECTED, UNKNOWN_USER
    ip_address = Column(String(45), default="127.0.0.1")
    details = Column(Text, nullable=True)

    user = relationship("User", back_populates="auth_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else "Unknown / Unregistered",
            "user_email": self.user.email if self.user else None,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "identity_score": round(self.identity_score, 4),
            "liveness_score": round(self.liveness_score, 4),
            "decision": self.decision,
            "ip_address": self.ip_address,
            "details": self.details
        }

class SpoofReport(Base):
    __tablename__ = "spoof_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    attack_type = Column(String(50), nullable=False) # printed_photo, mobile_screen, replay_video, 3d_mask
    confidence = Column(Float, default=0.0)
    frame_path = Column(String(256), nullable=True)
    frequency_score = Column(Float, default=0.0)
    color_score = Column(Float, default=0.0)
    temporal_score = Column(Float, default=0.0)
    ip_address = Column(String(45), default="127.0.0.1")

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "attack_type": self.attack_type,
            "confidence": round(self.confidence, 4),
            "frame_path": self.frame_path,
            "frequency_score": round(self.frequency_score, 4),
            "color_score": round(self.color_score, 4),
            "temporal_score": round(self.temporal_score, 4),
            "ip_address": self.ip_address
        }
