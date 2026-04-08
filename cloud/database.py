from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from typing import List, Dict, Optional
import json

Base = declarative_base()

class User(Base):
    """User model."""
    __tablename__ = 'users'

    id = Column(String(36), primary_key=True)
    name = Column(String(100))
    email = Column(String(100), unique=True)
    phone = Column(String(20), unique=True)
    registration_date = Column(DateTime, default=datetime.utcnow)
    total_reports = Column(Integer, default=0)
    valid_reports = Column(Integer, default=0)
    rewards_earned = Column(Float, default=0.0)
    trust_score = Column(Float, default=1.0)

class Violation(Base):
    """Violation model."""
    __tablename__ = 'violations'

    id = Column(String(36), primary_key=True)
    evidence_id = Column(String(36), unique=True)
    violation_type = Column(String(50))
    penalty_amount = Column(Float)
    license_plate = Column(String(20))
    timestamp = Column(DateTime)
    latitude = Column(Float)
    longitude = Column(Float)
    location_address = Column(Text)
    user_id = Column(String(36), ForeignKey('users.id'))
    status = Column(String(20), default='pending')  # pending, verified, rejected
    evidence_path = Column(String(255))
    ocr_confidence = Column(Float)
    detection_confidence = Column(Float)

    user = relationship("User")

class EChallan(Base):
    """E-Challan model."""
    __tablename__ = 'e_challans'

    id = Column(String(36), primary_key=True)
    violation_id = Column(String(36), ForeignKey('violations.id'))
    challan_number = Column(String(20), unique=True)
    amount = Column(Float)
    due_date = Column(DateTime)
    payment_status = Column(String(20), default='pending')  # pending, paid, overdue
    issued_date = Column(DateTime, default=datetime.utcnow)
    vehicle_number = Column(String(20))

    violation = relationship("Violation")

class Notification(Base):
    """Notification model."""
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey('users.id'))
    violation_id = Column(String(36), ForeignKey('violations.id'))
    type = Column(String(50))  # reward, challan, alert
    message = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)

class DatabaseManager:
    """Database manager for the traffic violation system."""

    def __init__(self, database_url: str = 'sqlite:///traffic_violation.db'):
        """
        Initialize database manager.

        Args:
            database_url: Database connection URL
        """
        self.engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_session(self):
        """Get database session."""
        return self.SessionLocal()

    def create_user(self, user_data: Dict) -> str:
        """Create new user."""
        session = self.get_session()
        try:
            user = User(**user_data)
            session.add(user)
            session.commit()
            return user.id
        finally:
            session.close()

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        session = self.get_session()
        try:
            return session.query(User).filter(User.id == user_id).first()
        finally:
            session.close()

    def update_user_stats(self, user_id: str, valid_report: bool = True):
        """Update user statistics."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.total_reports += 1
                if valid_report:
                    user.valid_reports += 1
                    accuracy = user.valid_reports / user.total_reports
                    user.trust_score = min(accuracy * 1.2, 1.0)
                session.commit()
        finally:
            session.close()

    def save_violation(self, violation_data: Dict) -> str:
        """Save violation report."""
        session = self.get_session()
        try:
            violation = Violation(**violation_data)
            session.add(violation)
            session.commit()
            return violation.id
        finally:
            session.close()

    def get_violations(self, user_id: str = None, status: str = None,
                       limit: int = 50) -> List[Violation]:
        """Get violations with optional filters."""
        session = self.get_session()
        try:
            query = session.query(Violation)
            if user_id:
                query = query.filter(Violation.user_id == user_id)
            if status:
                query = query.filter(Violation.status == status)
            return query.order_by(Violation.timestamp.desc()).limit(limit).all()
        finally:
            session.close()

    def create_e_challan(self, challan_data: Dict) -> str:
        """Create e-challan."""
        session = self.get_session()
        try:
            challan = EChallan(**challan_data)
            session.add(challan)
            session.commit()
            return challan.id
        finally:
            session.close()

    def update_payment_status(self, challan_id: str, status: str):
        """Update challan payment status."""
        session = self.get_session()
        try:
            challan = session.query(EChallan).filter(EChallan.id == challan_id).first()
            if challan:
                challan.payment_status = status
                session.commit()
        finally:
            session.close()

    def save_notification(self, notification_data: Dict) -> int:
        """Save notification."""
        session = self.get_session()
        try:
            notification = Notification(**notification_data)
            session.add(notification)
            session.commit()
            return notification.id
        finally:
            session.close()

    def get_notifications(self, user_id: str, unread_only: bool = False) -> List[Notification]:
        """Get user notifications."""
        session = self.get_session()
        try:
            query = session.query(Notification).filter(Notification.user_id == user_id)
            if unread_only:
                query = query.filter(Notification.read_at.is_(None))
            return query.order_by(Notification.sent_at.desc()).all()
        finally:
            session.close()

    def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics."""
        session = self.get_session()
        try:
            total_violations = session.query(Violation).count()
            pending_challans = session.query(EChallan).filter(EChallan.payment_status == 'pending').count()
            total_users = session.query(User).count()
            total_rewards = session.query(User).with_entities(User.rewards_earned).all()
            total_rewards_sum = sum(r[0] for r in total_rewards)

            return {
                'total_violations': total_violations,
                'pending_challans': pending_challans,
                'total_users': total_users,
                'total_rewards_distributed': total_rewards_sum
            }
        finally:
            session.close()