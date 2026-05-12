"""
Database configuration and models for Ecosystem Valuation Engine
"""

import os
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import psycopg2
import numpy as np

logger = logging.getLogger(__name__)
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text, Boolean, JSON, Index, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from sqlalchemy.dialects.postgresql import UUID
import streamlit as st

def convert_numpy_types(obj):
    """Recursively convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    return obj

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# SQLAlchemy setup - pool_pre_ping reconnects automatically if Neon drops idle connections
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # Test connection before use, reconnect if dropped
    pool_recycle=300,          # Recycle connections every 5 minutes
    pool_size=5,
    max_overflow=2,
    connect_args={"connect_timeout": 10}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    """Registered user accounts"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)
    organisation = Column(String(255), nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(64), nullable=True)
    verification_token_expiry = Column(DateTime, nullable=True)
    verification_reminder_sent_at = Column(DateTime, nullable=True)
    reset_token = Column(String(64), nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    # 'Pending' = signed up, awaiting verification (cannot log in)
    # 'Active'  = email verified, normal user
    # 'Removed' = soft-deleted after failing to verify within 48h; row retained
    #             for audit (email + display_name kept, credentials cleared)
    status = Column(String(16), default='Pending', nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_users_email', 'email'),
        Index('ix_users_verification_token', 'verification_token'),
        Index('ix_users_reset_token', 'reset_token'),
        Index('ix_users_status', 'status'),
    )


class EcosystemAnalysis(Base):
    """Store ecosystem analysis results"""
    __tablename__ = "ecosystem_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_session_id = Column(String(255), nullable=True)  # For tracking user sessions
    user_account_id = Column(UUID(as_uuid=True), nullable=True)  # Registered user FK
    project_type_id = Column(UUID(as_uuid=True), ForeignKey('pi_project_types.id'), nullable=True)
    area_name = Column(String(255), nullable=True)
    coordinates = Column(JSON, nullable=False)  # Store GeoJSON coordinates
    area_hectares = Column(Float, nullable=False)
    ecosystem_type = Column(String(255), nullable=False)
    total_value = Column(Float, nullable=False)
    value_per_hectare = Column(Float, nullable=False)
    analysis_results = Column(JSON, nullable=False)  # Store full analysis data
    sustainability_responses = Column(JSON, nullable=True)  # Store sustainability assessment responses
    sampling_points = Column(Integer, nullable=False, default=10)
    data_source = Column(String(255), nullable=False, default='ESVD')
    use_indicator_multipliers = Column(Boolean, nullable=False, default=False, server_default='false')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_ecosystem_analyses_user_session_id', 'user_session_id'),
        Index('ix_ecosystem_analyses_created_at', 'created_at'),
        Index('ix_ecosystem_analyses_user_account_id', 'user_account_id'),
    )

class SavedArea(Base):
    """Store user-saved areas for future analysis"""
    __tablename__ = "saved_areas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_session_id = Column(String(255), nullable=True)
    user_account_id = Column(UUID(as_uuid=True), nullable=True)  # Registered user FK
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    coordinates = Column(JSON, nullable=False)
    area_hectares = Column(Float, nullable=False)
    is_favorite = Column(Boolean, default=False)
    # Snapshot of the user's project-indicator configuration at save time:
    # which indicators they committed to, baseline/target scores, custom flags,
    # baseline/target dates, project ecosystem override. JSON for forward
    # compatibility — nullable so existing rows are unaffected.
    project_indicators = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_saved_areas_user_session_id', 'user_session_id'),
        Index('ix_saved_areas_user_account_id', 'user_account_id'),
    )

class AnalysisHistory(Base):
    """Store historical tracking for areas over time"""
    __tablename__ = "analysis_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    area_id = Column(UUID(as_uuid=True), nullable=True)  # Reference to SavedArea
    analysis_date = Column(DateTime, nullable=False)
    total_value = Column(Float, nullable=False)
    ecosystem_composition = Column(JSON, nullable=True)  # Track changes in ecosystem types
    environmental_factors = Column(JSON, nullable=True)  # Weather, climate data if available
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class NaturalCapitalBaseline(Base):
    """Store baseline natural capital values for ecosystem tracking"""
    __tablename__ = "natural_capital_baselines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    area_id = Column(UUID(as_uuid=True), nullable=True)  # Reference to SavedArea
    user_session_id = Column(String(255), nullable=True)
    user_account_id = Column(UUID(as_uuid=True), nullable=True)  # Registered user FK
    baseline_date = Column(DateTime, nullable=False)
    ecosystem_type = Column(String(255), nullable=False)
    
    # Core natural capital metrics
    total_baseline_value = Column(Float, nullable=False)
    provisioning_baseline = Column(Float, nullable=False, default=0)
    regulating_baseline = Column(Float, nullable=False, default=0)
    cultural_baseline = Column(Float, nullable=False, default=0)
    supporting_baseline = Column(Float, nullable=False, default=0)
    
    # Environmental indicators
    vegetation_health_index = Column(Float, nullable=True)  # NDVI or similar
    biodiversity_index = Column(Float, nullable=True)  # Shannon diversity
    carbon_stock_estimate = Column(Float, nullable=True)  # tons CO2 equivalent
    water_regulation_capacity = Column(Float, nullable=True)
    soil_quality_index = Column(Float, nullable=True)
    
    # Baseline metadata
    data_quality_score = Column(Float, nullable=True)  # 0-1 confidence score
    satellite_data_quality = Column(String(255), nullable=True)
    weather_conditions = Column(JSON, nullable=True)
    seasonal_adjustment = Column(Float, nullable=True)
    
    # Reference data
    coordinates = Column(JSON, nullable=False)
    area_hectares = Column(Float, nullable=False)
    sampling_points = Column(Integer, nullable=False)
    source_coefficients = Column(JSON, nullable=True)  # ESVD coefficients used
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NaturalCapitalTrend(Base):
    """Track natural capital changes over time"""
    __tablename__ = "natural_capital_trends"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    baseline_id = Column(UUID(as_uuid=True), nullable=False)  # Reference to baseline
    area_id = Column(UUID(as_uuid=True), nullable=True)
    user_account_id = Column(UUID(as_uuid=True), nullable=True)  # Registered user FK
    measurement_date = Column(DateTime, nullable=False)
    
    # Value changes from baseline
    total_value_change = Column(Float, nullable=False)  # Absolute change
    percent_change = Column(Float, nullable=False)  # Percentage change
    provisioning_change = Column(Float, nullable=False, default=0)
    regulating_change = Column(Float, nullable=False, default=0)
    cultural_change = Column(Float, nullable=False, default=0)
    supporting_change = Column(Float, nullable=False, default=0)
    
    # Environmental indicator changes
    vegetation_change = Column(Float, nullable=True)
    biodiversity_change = Column(Float, nullable=True)
    carbon_change = Column(Float, nullable=True)
    
    # Trend metadata
    trend_direction = Column(String(50), nullable=True)  # 'improving', 'declining', 'stable'
    confidence_level = Column(Float, nullable=True)  # Statistical confidence
    driving_factors = Column(JSON, nullable=True)  # Identified causes of change

    created_at = Column(DateTime, default=datetime.utcnow)


# ── Project Indicator (pi_*) models ──────────────────────────────────────────
# Project-typed structured field assessments. Seeded from
# utils/project_indicators_seed.py on first init. v1 is calc-neutral; v2+ will
# layer composite intactness aggregation, comparison vs EEI, and forecast.

class ProjectType(Base):
    __tablename__ = "pi_project_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(64), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(16), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Indicator(Base):
    __tablename__ = "pi_indicators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(64), unique=True, nullable=False)
    code = Column(String(8), nullable=False)
    name = Column(String(255), nullable=False)
    commitment_question = Column(Text, nullable=False)
    prospectus_scope_statement = Column(Text, nullable=False)
    baseline_question = Column(Text, nullable=False)
    why_matters = Column(Text, nullable=True)
    field_method = Column(Text, nullable=True)
    remote_sensing_alternative = Column(Text, nullable=True)
    sources = Column(Text, nullable=True)
    applicable_ecosystems = Column(JSON, nullable=True)
    is_mandatory = Column(Boolean, default=False, nullable=False)
    mapping_kind = Column(String(32), nullable=False, default='band_lookup')
    mapping_params = Column(JSON, nullable=False, default=dict)
    service_weights = Column(JSON, nullable=True)
    weight = Column(Float, default=1.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IndicatorBand(Base):
    __tablename__ = "pi_indicator_bands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    indicator_id = Column(UUID(as_uuid=True), ForeignKey('pi_indicators.id', ondelete='CASCADE'), nullable=False)
    score = Column(Float, nullable=False)
    label = Column(String(64), nullable=False)
    criteria = Column(Text, nullable=False)
    meaning = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False)

    __table_args__ = (
        Index('ix_pi_indicator_bands_indicator_id', 'indicator_id'),
        Index('ix_pi_indicator_bands_indicator_score', 'indicator_id', 'score', unique=True),
    )


class IndicatorFollowup(Base):
    __tablename__ = "pi_indicator_followups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    indicator_id = Column(UUID(as_uuid=True), ForeignKey('pi_indicators.id', ondelete='CASCADE'), nullable=False)
    slug = Column(String(64), nullable=False)
    question_text = Column(Text, nullable=False)
    input_kind = Column(String(16), nullable=False)
    options = Column(JSON, nullable=True)
    trigger_max_score = Column(Float, nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        Index('ix_pi_indicator_followups_indicator_slug', 'indicator_id', 'slug', unique=True),
    )


class ProjectTypeIndicator(Base):
    __tablename__ = "pi_project_type_indicators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_type_id = Column(UUID(as_uuid=True), ForeignKey('pi_project_types.id', ondelete='CASCADE'), nullable=False)
    indicator_id = Column(UUID(as_uuid=True), ForeignKey('pi_indicators.id'), nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    is_recommended = Column(Boolean, default=False, nullable=False)
    weight_override = Column(Float, nullable=True)

    __table_args__ = (
        Index('ix_pi_project_type_indicators_unique', 'project_type_id', 'indicator_id', unique=True),
    )


class AnalysisResponse(Base):
    __tablename__ = "pi_analysis_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey('ecosystem_analyses.id', ondelete='CASCADE'), nullable=False)
    project_type_id = Column(UUID(as_uuid=True), ForeignKey('pi_project_types.id'), nullable=False)
    indicator_id = Column(UUID(as_uuid=True), ForeignKey('pi_indicators.id'), nullable=False)
    is_committed = Column(Boolean, default=False, nullable=False)
    baseline_band_id = Column(UUID(as_uuid=True), ForeignKey('pi_indicator_bands.id'), nullable=True)
    baseline_score = Column(Float, nullable=True)
    baseline_year = Column(Integer, nullable=True)
    # Custom user-entered percentage stored as 0.0–1.0. NULL means the user
    # picked a predefined band (baseline_band_id/baseline_score path).
    # Calculations read coalesce(custom_score, baseline_score).
    custom_score = Column(Float, nullable=True)
    target_band_id = Column(UUID(as_uuid=True), ForeignKey('pi_indicator_bands.id'), nullable=True)
    target_score = Column(Float, nullable=True)
    target_year = Column(Integer, nullable=True)
    applies_to_ecosystem = Column(String(64), nullable=True)
    followup_responses = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_pi_analysis_responses_analysis_id', 'analysis_id'),
        Index('ix_pi_analysis_responses_unique',
              'analysis_id', 'indicator_id', 'applies_to_ecosystem', unique=True),
    )


class ComputedSubServiceMultiplier(Base):
    """Materialised per-sub-service multiplier output of the indicator
    multiplier engine. Regenerated whenever indicator responses change for
    an assessment; never edited by users."""
    __tablename__ = "computed_sub_service_multipliers"

    computation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True),
                         ForeignKey('ecosystem_analyses.id', ondelete='CASCADE'),
                         nullable=False)
    teeb_sub_service_key = Column(String(64), nullable=False)
    indicator_multiplier = Column(Float, nullable=True)        # weighted avg 0-1, NULL if fallback
    contributing_indicators = Column(JSON, nullable=False)     # list[str] indicator slugs
    contributing_response_pcts = Column(JSON, nullable=False)  # list[int] 0-100
    contributing_weights = Column(JSON, nullable=False)        # list[float]
    hd_multiplier = Column(Float, nullable=False, default=1.0, server_default='1.0')
    final_multiplier = Column(Float, nullable=False)           # what gets applied
    fallback_to_bbi = Column(Boolean, nullable=False)
    bbi_value_used = Column(Float, nullable=True)
    computed_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_computed_msm_analysis', 'analysis_id'),
    )


# Database utility functions
def initialize_user_session():
    """Initialize user session ID for database tracking"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    return st.session_state.user_id

@contextmanager
def get_db():
    """Context manager providing a database session with automatic rollback and cleanup."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_database():
    """Initialize database tables"""
    try:
        # Test connection first
        with engine.connect() as connection:
            pass

        # Create tables - but handle gracefully if they exist
        Base.metadata.create_all(bind=engine)

        # Idempotent seed of project-indicator taxonomy
        try:
            from utils.project_indicators_seed import seed_project_indicators
            with get_db() as db:
                seed_project_indicators(db)
        except Exception as seed_err:
            logger.warning(f"Project indicator seeding skipped: {seed_err}")

        return True
    except Exception as e:
        # Database not available - app should work without it
        logger.warning(f"Database initialization warning: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    try:
        with engine.connect() as connection:
            from sqlalchemy import text
            result = connection.execute(text("SELECT 1"))
            return True
    except Exception as e:
        # Don't show error message here - just return False
        # Error will be shown elsewhere if needed
        return False

def _get_auth_user_id() -> Optional[str]:
    """Return the logged-in user's UUID string, or None."""
    try:
        if hasattr(st, 'session_state'):
            auth_user = st.session_state.get('auth_user')
            if auth_user and isinstance(auth_user, dict):
                return auth_user.get('id')
    except Exception:
        pass
    return None


class UserDB:
    """Database operations for registered user accounts."""

    @staticmethod
    def _user_dict(user: 'User') -> Dict:
        return {
            'id': str(user.id),
            'email': user.email,
            'display_name': user.display_name,
            'organisation': user.organisation,
            'email_verified': bool(user.email_verified),
            'is_admin': bool(user.is_admin),
            'status': user.status or 'Pending',
        }

    @staticmethod
    def list_all_users() -> list:
        """Return all registered users for admin display. The caller is
        responsible for verifying that the requester is an admin."""
        try:
            with get_db() as db:
                users = db.query(User).order_by(User.created_at.desc()).all()
                return [
                    {
                        'email': u.email,
                        'display_name': u.display_name,
                        'organisation': u.organisation,
                        'email_verified': bool(u.email_verified),
                        'is_admin': bool(u.is_admin),
                        'status': u.status or 'Pending',
                        'created_at': u.created_at,
                    }
                    for u in users
                ]
        except Exception as e:
            logger.error(f"list_all_users failed: {e}")
            return []

    @staticmethod
    def register(email: str, password: str, display_name: Optional[str] = None,
                 organisation: Optional[str] = None) -> Dict:
        """Create a new user (status='Pending') and send the verification email.
        If the email already belongs to a soft-deleted ('Removed') row, that row
        is reused: password, display name and organisation are overwritten and
        the account returns to 'Pending' awaiting fresh verification.

        Returns the user dict. The caller MUST NOT log the user in — the account
        cannot be used until the verification link is clicked.
        Raises ValueError if an Active or Pending account already exists.
        """
        import bcrypt
        import secrets
        try:
            with get_db() as db:
                existing = db.query(User).filter(User.email == email.lower()).first()
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                token = secrets.token_urlsafe(32)
                expiry = datetime.utcnow() + timedelta(hours=24)

                if existing:
                    if existing.status == 'Removed':
                        # Reactivate the soft-deleted row.
                        existing.password_hash = password_hash
                        existing.display_name = display_name
                        existing.organisation = organisation
                        existing.email_verified = False
                        existing.verification_token = token
                        existing.verification_token_expiry = expiry
                        existing.verification_reminder_sent_at = None
                        existing.status = 'Pending'
                        existing.created_at = datetime.utcnow()  # restart the 24h clock
                        db.commit()
                        db.refresh(existing)
                        user = existing
                    else:
                        raise ValueError("An account with that email address already exists.")
                else:
                    user = User(
                        email=email.lower(),
                        password_hash=password_hash,
                        display_name=display_name,
                        organisation=organisation,
                        email_verified=False,
                        verification_token=token,
                        verification_token_expiry=expiry,
                        status='Pending',
                    )
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                try:
                    from utils.email_utils import send_verification_email
                    send_verification_email(user.email, token)
                except Exception as e:
                    logger.warning(f"Verification email failed: {e}")
                return UserDB._user_dict(user)
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            raise

    @staticmethod
    def login(email: str, password: str) -> tuple:
        """Verify credentials and return (user_dict, error_code).
        error_code is None on success, or one of:
            'invalid_credentials' — email not found or wrong password
            'pending_verification' — credentials OK but email not verified
            'removed' — account has been soft-deleted
        """
        import bcrypt
        try:
            with get_db() as db:
                user = db.query(User).filter(User.email == email.lower()).first()
                if not user:
                    return None, 'invalid_credentials'
                # Removed accounts have password_hash cleared, so the bcrypt
                # check below would fail anyway — but be explicit about state.
                if user.status == 'Removed':
                    return None, 'removed'
                if not user.password_hash or not bcrypt.checkpw(
                    password.encode('utf-8'), user.password_hash.encode('utf-8')
                ):
                    return None, 'invalid_credentials'
                if user.status != 'Active':
                    return None, 'pending_verification'
                return UserDB._user_dict(user), None
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return None, 'invalid_credentials'

    @staticmethod
    def get_by_id(user_id: str) -> Optional[Dict]:
        """Return user dict by UUID string, or None."""
        try:
            with get_db() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return None
                return UserDB._user_dict(user)
        except Exception as e:
            logger.error(f"get_by_id failed: {e}")
            return None

    @staticmethod
    def verify_email(token: str) -> bool:
        """Mark email as verified and promote the account to Active. Returns
        True on success, False if the token is invalid/expired/removed."""
        try:
            with get_db() as db:
                user = db.query(User).filter(User.verification_token == token).first()
                if not user:
                    return False
                if user.status == 'Removed':
                    return False
                if user.verification_token_expiry and user.verification_token_expiry < datetime.utcnow():
                    return False
                user.email_verified = True
                user.verification_token = None
                user.verification_token_expiry = None
                user.verification_reminder_sent_at = None
                user.status = 'Active'
                db.commit()
                return True
        except Exception as e:
            logger.error(f"verify_email failed: {e}")
            return False

    @staticmethod
    def create_password_reset(email: str) -> bool:
        """Generate a reset token, persist it, and email a reset link. Returns True if the
        email was found (regardless of whether the SMTP send succeeded)."""
        import secrets
        try:
            with get_db() as db:
                user = db.query(User).filter(User.email == email.lower()).first()
                if not user:
                    return False
                token = secrets.token_urlsafe(32)
                user.reset_token = token
                user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
                db.commit()
                try:
                    from utils.email_utils import send_password_reset_email
                    send_password_reset_email(user.email, token)
                except Exception as e:
                    logger.warning(f"Password reset email failed: {e}")
                return True
        except Exception as e:
            logger.error(f"create_password_reset failed: {e}")
            return False

    @staticmethod
    def reset_password(token: str, new_password: str) -> bool:
        """Set a new password using a valid reset token. Returns True on success."""
        import bcrypt
        try:
            with get_db() as db:
                user = db.query(User).filter(User.reset_token == token).first()
                if not user:
                    return False
                if user.reset_token_expiry and user.reset_token_expiry < datetime.utcnow():
                    return False
                user.password_hash = bcrypt.hashpw(
                    new_password.encode('utf-8'), bcrypt.gensalt()
                ).decode('utf-8')
                user.reset_token = None
                user.reset_token_expiry = None
                db.commit()
                return True
        except Exception as e:
            logger.error(f"reset_password failed: {e}")
            return False

    @staticmethod
    def resend_verification(email: str) -> bool:
        """Regenerate and resend the verification email for a Pending account.
        Returns False for unknown emails, already-Active accounts, and Removed
        accounts (the latter must re-register)."""
        import secrets
        try:
            with get_db() as db:
                user = db.query(User).filter(User.email == email.lower()).first()
                if not user or user.email_verified or user.status != 'Pending':
                    return False
                token = secrets.token_urlsafe(32)
                user.verification_token = token
                user.verification_token_expiry = datetime.utcnow() + timedelta(hours=24)
                db.commit()
                from utils.email_utils import send_verification_email
                send_verification_email(user.email, token)
                return True
        except Exception as e:
            logger.error(f"resend_verification failed: {e}")
            return False

    @staticmethod
    def process_unverified_accounts() -> Dict[str, int]:
        """Daily lifecycle pass.

        Phase 1 — Unverified > 24h, no reminder sent yet:
            Regenerate the verification token, send the 'final warning' email,
            stamp verification_reminder_sent_at = now.

        Phase 2 — Reminder sent > 24h ago, still unverified:
            Soft-delete: status='Removed', clear password_hash and tokens,
            keep email + display_name for the audit log.

        Returns a counts dict: {'reminded': N, 'removed': M, 'errors': E}.
        Designed to run from a Cloud Run Job triggered by Cloud Scheduler.
        """
        import secrets
        reminded = removed = errors = 0
        now = datetime.utcnow()
        try:
            with get_db() as db:
                # ─── Phase 1: send the final-warning reminder ────────────────
                reminder_due = db.query(User).filter(
                    User.status == 'Pending',
                    User.created_at < now - timedelta(hours=24),
                    User.verification_reminder_sent_at.is_(None),
                ).all()
                for user in reminder_due:
                    try:
                        token = secrets.token_urlsafe(32)
                        user.verification_token = token
                        user.verification_token_expiry = now + timedelta(hours=24)
                        user.verification_reminder_sent_at = now
                        db.commit()
                        from utils.email_utils import send_final_verification_warning_email
                        send_final_verification_warning_email(user.email, token)
                        reminded += 1
                    except Exception as e:
                        errors += 1
                        logger.error(f"reminder send failed for {user.email}: {e}")
                        db.rollback()

                # ─── Phase 2: soft-delete after another 24h of silence ──────
                delete_due = db.query(User).filter(
                    User.status == 'Pending',
                    User.verification_reminder_sent_at.isnot(None),
                    User.verification_reminder_sent_at < now - timedelta(hours=24),
                ).all()
                for user in delete_due:
                    try:
                        user.status = 'Removed'
                        user.password_hash = ''
                        user.verification_token = None
                        user.verification_token_expiry = None
                        user.reset_token = None
                        user.reset_token_expiry = None
                        db.commit()
                        removed += 1
                    except Exception as e:
                        errors += 1
                        logger.error(f"soft-delete failed for {user.email}: {e}")
                        db.rollback()
        except Exception as e:
            logger.error(f"process_unverified_accounts failed: {e}")
            errors += 1
        return {'reminded': reminded, 'removed': removed, 'errors': errors}


# Database operations for ecosystem analyses
class EcosystemAnalysisDB:
    """Database operations for ecosystem analyses"""
    
    @staticmethod
    def save_analysis(
        coordinates: List[List[float]],
        area_hectares: float,
        ecosystem_type: str,
        total_value: float,
        value_per_hectare: float,
        analysis_results: Dict[str, Any],
        sampling_points: int = 10,
        area_name: Optional[str] = None,
        user_session_id: Optional[str] = None,
        sustainability_responses: Optional[Dict[str, Any]] = None,
        project_type_slug: Optional[str] = None,
    ) -> Optional[str]:
        """Save ecosystem analysis to database"""
        try:
            with get_db() as db:
                session_user_id = None
                try:
                    if hasattr(st, 'session_state') and 'user_id' in st.session_state:
                        session_user_id = st.session_state.get('user_id')
                except Exception as e:
                    logger.warning(f"Could not access session state for user_id: {e}")

                auth_user_id = _get_auth_user_id()

                project_type_id = None
                if project_type_slug:
                    pt = db.query(ProjectType).filter(ProjectType.slug == project_type_slug).first()
                    if pt:
                        project_type_id = pt.id

                clean_coordinates = convert_numpy_types(coordinates)
                clean_analysis_results = convert_numpy_types(analysis_results)
                clean_sustainability_responses = convert_numpy_types(sustainability_responses) if sustainability_responses else None
                clean_area_hectares = float(area_hectares) if isinstance(area_hectares, np.floating) else area_hectares
                clean_total_value = float(total_value) if isinstance(total_value, np.floating) else total_value
                clean_value_per_hectare = float(value_per_hectare) if isinstance(value_per_hectare, np.floating) else value_per_hectare

                analysis = EcosystemAnalysis(
                    user_session_id=user_session_id or session_user_id,
                    user_account_id=auth_user_id,
                    project_type_id=project_type_id,
                    area_name=area_name,
                    coordinates=clean_coordinates,
                    area_hectares=clean_area_hectares,
                    ecosystem_type=ecosystem_type,
                    total_value=clean_total_value,
                    value_per_hectare=clean_value_per_hectare,
                    analysis_results=clean_analysis_results,
                    sustainability_responses=clean_sustainability_responses,
                    sampling_points=sampling_points,
                    data_source=clean_analysis_results.get('data_source', 'ESVD/TEEB Database')
                )

                db.add(analysis)
                db.commit()
                db.refresh(analysis)
                return str(analysis.id)

        except Exception as e:
            import traceback
            error_msg = f"Failed to save analysis: {str(e)}"
            traceback_msg = f"Traceback: {traceback.format_exc()}"
            logger.error(f"{error_msg}\n{traceback_msg}")
            try:
                if hasattr(st, 'error'):
                    st.error(error_msg)
                    st.error(traceback_msg)
            except Exception:
                print(error_msg)
                print(traceback_msg)
            return None
    
    @staticmethod
    def get_user_analyses(user_session_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get user's recent analyses"""
        try:
            with get_db() as db:
                session_user_id = None
                try:
                    if hasattr(st, 'session_state') and 'user_id' in st.session_state:
                        session_user_id = st.session_state.get('user_id')
                except Exception as e:
                    logger.warning(f"Could not access session state for user_id: {e}")

                auth_user_id = _get_auth_user_id()
                if auth_user_id:
                    analyses = db.query(EcosystemAnalysis).filter(
                        EcosystemAnalysis.user_account_id == auth_user_id
                    ).order_by(EcosystemAnalysis.created_at.desc()).limit(limit).all()
                else:
                    session_id = user_session_id or session_user_id
                    if not session_id:
                        return []
                    analyses = db.query(EcosystemAnalysis).filter(
                        EcosystemAnalysis.user_session_id == session_id
                    ).order_by(EcosystemAnalysis.created_at.desc()).limit(limit).all()

                return [
                    {
                        'id': str(a.id),
                        'area_name': a.area_name,
                        'ecosystem_type': a.ecosystem_type,
                        'total_value': a.total_value,
                        'area_hectares': a.area_hectares,
                        'created_at': a.created_at,
                        'coordinates': a.coordinates,
                    }
                    for a in analyses
                ]

        except Exception as e:
            logger.error(f"Failed to retrieve analyses: {e}")
            try:
                if hasattr(st, 'error'):
                    st.error(f"Failed to retrieve analyses: {str(e)}")
            except Exception:
                print(f"Failed to retrieve analyses: {str(e)}")
            return []

    @staticmethod
    def get_analysis_by_id(analysis_id: str) -> Optional[Dict]:
        """Get specific analysis by ID"""
        try:
            with get_db() as db:
                analysis = db.query(EcosystemAnalysis).filter(
                    EcosystemAnalysis.id == analysis_id
                ).first()

                if not analysis:
                    return None
                return {
                    'id': str(analysis.id),
                    'area_name': analysis.area_name,
                    'coordinates': analysis.coordinates,
                    'area_hectares': analysis.area_hectares,
                    'ecosystem_type': analysis.ecosystem_type,
                    'total_value': analysis.total_value,
                    'value_per_hectare': analysis.value_per_hectare,
                    'analysis_results': analysis.analysis_results,
                    'sampling_points': analysis.sampling_points,
                    'created_at': analysis.created_at,
                }

        except Exception as e:
            logger.error(f"Failed to retrieve analysis: {e}")
            try:
                if hasattr(st, 'error'):
                    st.error(f"Failed to retrieve analysis: {str(e)}")
            except Exception:
                print(f"Failed to retrieve analysis: {str(e)}")
            return None

# Database operations for saved areas
class SavedAreaDB:
    """Database operations for saved areas"""
    
    @staticmethod
    def save_area(
        name: str,
        coordinates: List[List[float]],
        area_hectares: float,
        description: Optional[str] = None,
        user_session_id: Optional[str] = None,
        project_indicators: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Save area for future analysis.

        ``project_indicators`` (optional) is a JSON-serialisable dict capturing
        the user's indicator-multiplier configuration at save time, so it can
        be restored when the area is loaded later. See
        ``app.py::_build_indicator_state_blob`` for the canonical shape.
        """
        try:
            with get_db() as db:
                session_user_id = None
                try:
                    if hasattr(st, 'session_state') and 'user_id' in st.session_state:
                        session_user_id = st.session_state.get('user_id')
                except Exception as e:
                    logger.warning(f"Could not access session state for user_id: {e}")

                auth_user_id = _get_auth_user_id()

                saved_area = SavedArea(
                    user_session_id=user_session_id or session_user_id,
                    user_account_id=auth_user_id,
                    name=name,
                    description=description,
                    coordinates=convert_numpy_types(coordinates),
                    area_hectares=float(area_hectares),
                    project_indicators=(convert_numpy_types(project_indicators)
                                        if project_indicators else None),
                )

                db.add(saved_area)
                db.commit()
                db.refresh(saved_area)
                return str(saved_area.id)

        except Exception as e:
            import traceback
            error_msg = f"Failed to save area: {str(e)}"
            traceback_msg = f"Traceback: {traceback.format_exc()}"
            logger.error(f"{error_msg}\n{traceback_msg}")
            try:
                if hasattr(st, 'error'):
                    st.error(error_msg)
                    st.error(traceback_msg)
            except Exception:
                print(error_msg)
                print(traceback_msg)
            return None

    @staticmethod
    def get_user_saved_areas(user_session_id: Optional[str] = None) -> List[Dict]:
        """Get user's saved areas"""
        try:
            with get_db() as db:
                session_user_id = None
                try:
                    if hasattr(st, 'session_state') and 'user_id' in st.session_state:
                        session_user_id = st.session_state.get('user_id')
                except Exception as e:
                    logger.warning(f"Could not access session state for user_id: {e}")

                auth_user_id = _get_auth_user_id()
                if auth_user_id:
                    areas = db.query(SavedArea).filter(
                        SavedArea.user_account_id == auth_user_id
                    ).order_by(SavedArea.updated_at.desc()).all()
                else:
                    session_id = user_session_id or session_user_id
                    if not session_id:
                        return []
                    areas = db.query(SavedArea).filter(
                        SavedArea.user_session_id == session_id
                    ).order_by(SavedArea.updated_at.desc()).all()

                return [
                    {
                        'id': str(a.id),
                        'name': a.name,
                        'description': a.description,
                        'coordinates': a.coordinates,
                        'area_hectares': a.area_hectares,
                        'is_favorite': a.is_favorite,
                        'project_indicators': a.project_indicators,
                        'created_at': a.created_at,
                    }
                    for a in areas
                ]

        except Exception as e:
            logger.error(f"Failed to retrieve saved areas: {e}")
            try:
                if hasattr(st, 'error'):
                    st.error(f"Failed to retrieve saved areas: {str(e)}")
            except Exception:
                print(f"Failed to retrieve saved areas: {str(e)}")
            return []

    @staticmethod
    def delete_area(area_id: str) -> bool:
        """Delete a saved area; only succeeds if it belongs to the current user."""
        try:
            with get_db() as db:
                query = db.query(SavedArea).filter(SavedArea.id == area_id)
                auth_user_id = _get_auth_user_id()
                if auth_user_id:
                    query = query.filter(SavedArea.user_account_id == auth_user_id)
                else:
                    try:
                        session_id = st.session_state.get('user_id') if hasattr(st, 'session_state') else None
                    except Exception:
                        session_id = None
                    if session_id:
                        query = query.filter(SavedArea.user_session_id == session_id)
                area = query.first()
                if area:
                    db.delete(area)
                    db.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to delete area: {e}")
            return False


# Database operations for natural capital baselines
class NaturalCapitalBaselineDB:
    """Database operations for natural capital baselines"""
    
    @staticmethod
    def create_baseline(
        coordinates: List[List[float]],
        area_hectares: float,
        ecosystem_type: str,
        analysis_results: Dict[str, Any],
        sampling_points: int,
        area_id: Optional[str] = None,
        user_session_id: Optional[str] = None
    ) -> Optional[str]:
        """Create a natural capital baseline from analysis results"""
        try:
            with get_db() as db:
                esvd_data = analysis_results.get('esvd_results', {})
                provisioning = esvd_data.get('provisioning', {}).get('total', 0)
                regulating = esvd_data.get('regulating', {}).get('total', 0)
                cultural = esvd_data.get('cultural', {}).get('total', 0)
                supporting = esvd_data.get('supporting', {}).get('total', 0)

                detected_ecosystem = st.session_state.get('detected_ecosystem', {})
                vegetation_health = detected_ecosystem.get('confidence', 0.5)
                biodiversity_index = 0

                if 'ecosystem_distribution' in detected_ecosystem:
                    import math
                    ecosystem_distribution = detected_ecosystem['ecosystem_distribution']
                    total_points = detected_ecosystem.get('successful_queries', 1)
                    for eco_type, data in ecosystem_distribution.items():
                        proportion = data['count'] / total_points
                        if proportion > 0:
                            biodiversity_index -= proportion * math.log(proportion)

                baseline = NaturalCapitalBaseline(
                    area_id=area_id,
                    user_session_id=user_session_id or st.session_state.get('user_id'),
                    user_account_id=_get_auth_user_id(),
                    baseline_date=datetime.utcnow(),
                    ecosystem_type=ecosystem_type,
                    total_baseline_value=analysis_results['total_value'],
                    provisioning_baseline=provisioning,
                    regulating_baseline=regulating,
                    cultural_baseline=cultural,
                    supporting_baseline=supporting,
                    vegetation_health_index=vegetation_health,
                    biodiversity_index=biodiversity_index,
                    data_quality_score=detected_ecosystem.get('confidence', 0.5),
                    coordinates=coordinates,
                    area_hectares=area_hectares,
                    sampling_points=sampling_points,
                    source_coefficients=esvd_data
                )

                db.add(baseline)
                db.commit()
                db.refresh(baseline)
                return str(baseline.id)

        except Exception as e:
            st.error(f"Failed to create baseline: {str(e)}")
            return None
    
    @staticmethod
    def get_area_baseline(area_id: str) -> Optional[Dict]:
        """Get the most recent baseline for an area"""
        try:
            with get_db() as db:
                baseline = db.query(NaturalCapitalBaseline).filter(
                    NaturalCapitalBaseline.area_id == area_id
                ).order_by(NaturalCapitalBaseline.baseline_date.desc()).first()

                if not baseline:
                    return None
                return {
                    'id': str(baseline.id),
                    'baseline_date': baseline.baseline_date,
                    'ecosystem_type': baseline.ecosystem_type,
                    'total_baseline_value': baseline.total_baseline_value,
                    'provisioning_baseline': baseline.provisioning_baseline,
                    'regulating_baseline': baseline.regulating_baseline,
                    'cultural_baseline': baseline.cultural_baseline,
                    'supporting_baseline': baseline.supporting_baseline,
                    'vegetation_health_index': baseline.vegetation_health_index,
                    'biodiversity_index': baseline.biodiversity_index,
                    'area_hectares': baseline.area_hectares,
                    'data_quality_score': baseline.data_quality_score,
                }

        except Exception as e:
            st.error(f"Failed to retrieve baseline: {str(e)}")
            return None
    
    @staticmethod
    def compare_to_baseline(
        current_analysis: Dict[str, Any],
        baseline_id: str
    ) -> Optional[Dict]:
        """Compare current analysis to baseline and create trend data"""
        try:
            with get_db() as db:
                baseline = db.query(NaturalCapitalBaseline).filter(
                    NaturalCapitalBaseline.id == baseline_id
                ).first()

                if baseline is None:
                    return None

                baseline_value = float(baseline.total_baseline_value) if baseline.total_baseline_value is not None else 0.0
                current_value = float(current_analysis['total_value'])
                total_change = current_value - baseline_value
                percent_change = (total_change / baseline_value) * 100 if baseline_value > 0 else 0

                if abs(percent_change) < 5:
                    trend_direction = 'stable'
                elif percent_change > 0:
                    trend_direction = 'improving'
                else:
                    trend_direction = 'declining'

                esvd_data = current_analysis.get('esvd_results', {})
                current_provisioning = esvd_data.get('provisioning', {}).get('total', 0)
                current_regulating = esvd_data.get('regulating', {}).get('total', 0)
                current_cultural = esvd_data.get('cultural', {}).get('total', 0)
                current_supporting = esvd_data.get('supporting', {}).get('total', 0)

                provisioning_change = current_provisioning - (baseline.provisioning_baseline or 0.0)
                regulating_change = current_regulating - (baseline.regulating_baseline or 0.0)
                cultural_change = current_cultural - (baseline.cultural_baseline or 0.0)
                supporting_change = current_supporting - (baseline.supporting_baseline or 0.0)

                trend = NaturalCapitalTrend(
                    baseline_id=baseline_id,
                    area_id=baseline.area_id,
                    measurement_date=datetime.utcnow(),
                    total_value_change=total_change,
                    percent_change=percent_change,
                    provisioning_change=provisioning_change,
                    regulating_change=regulating_change,
                    cultural_change=cultural_change,
                    supporting_change=supporting_change,
                    trend_direction=trend_direction,
                    confidence_level=current_analysis.get('data_quality_score', 0.5)
                )

                db.add(trend)
                db.commit()
                db.refresh(trend)

                return {
                    'trend_id': str(trend.id),
                    'baseline_date': baseline.baseline_date,
                    'measurement_date': trend.measurement_date,
                    'total_change': total_change,
                    'percent_change': percent_change,
                    'trend_direction': trend_direction,
                    'service_changes': {
                        'provisioning': provisioning_change,
                        'regulating': regulating_change,
                        'cultural': cultural_change,
                        'supporting': supporting_change,
                    },
                    'baseline_values': {
                        'total': baseline.total_baseline_value,
                        'provisioning': baseline.provisioning_baseline,
                        'regulating': baseline.regulating_baseline,
                        'cultural': baseline.cultural_baseline,
                        'supporting': baseline.supporting_baseline,
                    },
                }

        except Exception as e:
            st.error(f"Failed to compare to baseline: {str(e)}")
            return None

# ── Project Indicator DB access ──────────────────────────────────────────────

class ProjectIndicatorDB:
    """Database operations for project-typed indicator commitments and responses."""

    @staticmethod
    def get_active_project_types() -> List[Dict]:
        try:
            with get_db() as db:
                rows = db.query(ProjectType).filter(
                    ProjectType.is_active == True
                ).order_by(ProjectType.sort_order, ProjectType.name).all()
                return [
                    {'id': str(r.id), 'slug': r.slug, 'name': r.name,
                     'icon': r.icon, 'description': r.description,
                     'sort_order': r.sort_order}
                    for r in rows
                ]
        except Exception as e:
            logger.error(f"get_active_project_types failed: {e}")
            return []

    @staticmethod
    def get_project_type_with_indicators(slug: str) -> Optional[Dict]:
        """Return project type + ordered indicators + bands + followups in one call."""
        try:
            with get_db() as db:
                pt = db.query(ProjectType).filter(ProjectType.slug == slug).first()
                if not pt:
                    return None
                joins = (
                    db.query(ProjectTypeIndicator, Indicator)
                    .join(Indicator, ProjectTypeIndicator.indicator_id == Indicator.id)
                    .filter(ProjectTypeIndicator.project_type_id == pt.id,
                            Indicator.is_active == True)
                    .order_by(ProjectTypeIndicator.sort_order)
                    .all()
                )
                indicators = []
                for join, ind in joins:
                    bands = (
                        db.query(IndicatorBand)
                        .filter(IndicatorBand.indicator_id == ind.id)
                        .order_by(IndicatorBand.sort_order)
                        .all()
                    )
                    followups = (
                        db.query(IndicatorFollowup)
                        .filter(IndicatorFollowup.indicator_id == ind.id)
                        .order_by(IndicatorFollowup.sort_order)
                        .all()
                    )
                    indicators.append({
                        'id': str(ind.id),
                        'slug': ind.slug,
                        'code': ind.code,
                        'name': ind.name,
                        'commitment_question': ind.commitment_question,
                        'prospectus_scope_statement': ind.prospectus_scope_statement,
                        'baseline_question': ind.baseline_question,
                        'why_matters': ind.why_matters,
                        'field_method': ind.field_method,
                        'remote_sensing_alternative': ind.remote_sensing_alternative,
                        'sources': ind.sources,
                        'applicable_ecosystems': ind.applicable_ecosystems,
                        'is_mandatory': bool(ind.is_mandatory),
                        'mapping_kind': ind.mapping_kind,
                        'service_weights': ind.service_weights or {},
                        'weight': float(ind.weight),
                        'sort_order': join.sort_order,
                        'is_recommended': bool(join.is_recommended),
                        'weight_override': float(join.weight_override) if join.weight_override is not None else None,
                        'bands': [
                            {'id': str(b.id), 'score': float(b.score),
                             'label': b.label, 'criteria': b.criteria,
                             'meaning': b.meaning, 'sort_order': b.sort_order}
                            for b in bands
                        ],
                        'followups': [
                            {'id': str(f.id), 'slug': f.slug,
                             'question_text': f.question_text,
                             'input_kind': f.input_kind,
                             'options': f.options,
                             'trigger_max_score': float(f.trigger_max_score) if f.trigger_max_score is not None else None,
                             'sort_order': f.sort_order}
                            for f in followups
                        ],
                    })
                return {
                    'id': str(pt.id),
                    'slug': pt.slug,
                    'name': pt.name,
                    'icon': pt.icon,
                    'description': pt.description,
                    'indicators': indicators,
                }
        except Exception as e:
            logger.error(f"get_project_type_with_indicators failed: {e}")
            return None

    @staticmethod
    def set_analysis_project_type(analysis_id: str, project_type_slug: Optional[str]) -> bool:
        try:
            with get_db() as db:
                analysis = db.query(EcosystemAnalysis).filter(
                    EcosystemAnalysis.id == analysis_id
                ).first()
                if not analysis:
                    return False
                if project_type_slug:
                    pt = db.query(ProjectType).filter(ProjectType.slug == project_type_slug).first()
                    analysis.project_type_id = pt.id if pt else None
                else:
                    analysis.project_type_id = None
                db.commit()
                return True
        except Exception as e:
            logger.error(f"set_analysis_project_type failed: {e}")
            return False

    @staticmethod
    def save_commitments(analysis_id: str, project_type_slug: str,
                         committed_indicator_slugs: List[str]) -> bool:
        """Upsert is_committed flag per indicator. Append-only: once an
        indicator's row has is_committed=True it cannot be flipped back to
        False — committing to monitor an indicator is a durable promise.
        Indicators not in the list and not yet committed get a row with
        is_committed=False so measurement scaffolding exists. Mandatory
        indicators (e.g. HD) are always committed."""
        try:
            with get_db() as db:
                pt = db.query(ProjectType).filter(ProjectType.slug == project_type_slug).first()
                if not pt:
                    return False
                joins = (
                    db.query(ProjectTypeIndicator, Indicator)
                    .join(Indicator, ProjectTypeIndicator.indicator_id == Indicator.id)
                    .filter(ProjectTypeIndicator.project_type_id == pt.id)
                    .all()
                )
                committed_set = set(committed_indicator_slugs or [])
                for _, ind in joins:
                    desired_now = (ind.slug in committed_set) or bool(ind.is_mandatory)
                    existing = db.query(AnalysisResponse).filter(
                        AnalysisResponse.analysis_id == analysis_id,
                        AnalysisResponse.indicator_id == ind.id,
                        AnalysisResponse.applies_to_ecosystem.is_(None),
                    ).first()
                    if existing:
                        # Append-only: do not flip True → False. Allow False → True.
                        if existing.is_committed and not desired_now:
                            continue
                        existing.is_committed = desired_now
                        existing.project_type_id = pt.id
                    else:
                        db.add(AnalysisResponse(
                            analysis_id=analysis_id,
                            project_type_id=pt.id,
                            indicator_id=ind.id,
                            is_committed=desired_now,
                        ))
                db.commit()
                return True
        except Exception as e:
            logger.error(f"save_commitments failed: {e}")
            return False

    @staticmethod
    def save_response(analysis_id: str, project_type_slug: str, indicator_slug: str,
                      baseline_band_id: Optional[str], baseline_year: Optional[int],
                      target_band_id: Optional[str], target_year: Optional[int],
                      applies_to_ecosystem: Optional[str],
                      followup_responses: Optional[Dict[str, Any]],
                      notes: Optional[str],
                      custom_score: Optional[float] = None) -> Optional[str]:
        """Upsert a measurement row for (analysis, indicator, applies_to_ecosystem).

        Either a band (via ``baseline_band_id``) OR a custom percentage (via
        ``custom_score``, range 0.0–1.0) is stored — never both. If
        ``custom_score`` is provided, ``baseline_band_id`` and ``baseline_score``
        are cleared. Calc code reads ``coalesce(custom_score, baseline_score)``.
        """
        try:
            with get_db() as db:
                pt = db.query(ProjectType).filter(ProjectType.slug == project_type_slug).first()
                ind = db.query(Indicator).filter(Indicator.slug == indicator_slug).first()
                if not pt or not ind:
                    return None

                # Mutually exclusive: custom_score wins, band fields cleared
                if custom_score is not None:
                    baseline_band_id = None
                    baseline_score = None
                else:
                    baseline_score = None
                    if baseline_band_id:
                        b = db.query(IndicatorBand).filter(IndicatorBand.id == baseline_band_id).first()
                        if b:
                            baseline_score = float(b.score)
                target_score = None
                if target_band_id:
                    b = db.query(IndicatorBand).filter(IndicatorBand.id == target_band_id).first()
                    if b:
                        target_score = float(b.score)

                existing = db.query(AnalysisResponse).filter(
                    AnalysisResponse.analysis_id == analysis_id,
                    AnalysisResponse.indicator_id == ind.id,
                    AnalysisResponse.applies_to_ecosystem == applies_to_ecosystem,
                ).first()
                if existing:
                    existing.project_type_id = pt.id
                    existing.is_committed = True
                    existing.baseline_band_id = baseline_band_id
                    existing.baseline_score = baseline_score
                    existing.baseline_year = baseline_year
                    existing.target_band_id = target_band_id
                    existing.target_score = target_score
                    existing.target_year = target_year
                    existing.custom_score = custom_score
                    existing.followup_responses = followup_responses
                    existing.notes = notes
                    db.commit()
                    return str(existing.id)
                row = AnalysisResponse(
                    analysis_id=analysis_id,
                    project_type_id=pt.id,
                    indicator_id=ind.id,
                    is_committed=True,
                    baseline_band_id=baseline_band_id,
                    baseline_score=baseline_score,
                    baseline_year=baseline_year,
                    target_band_id=target_band_id,
                    target_score=target_score,
                    target_year=target_year,
                    custom_score=custom_score,
                    applies_to_ecosystem=applies_to_ecosystem,
                    followup_responses=followup_responses,
                    notes=notes,
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                return str(row.id)
        except Exception as e:
            logger.error(f"save_response failed: {e}")
            return None

    @staticmethod
    def get_assessment_flag(analysis_id: str) -> bool:
        """Return EcosystemAnalysis.use_indicator_multipliers for the given
        analysis. False if the analysis doesn't exist."""
        try:
            with get_db() as db:
                row = db.query(EcosystemAnalysis).filter(
                    EcosystemAnalysis.id == analysis_id
                ).first()
                return bool(row.use_indicator_multipliers) if row else False
        except Exception as e:
            logger.error(f"get_assessment_flag failed: {e}")
            return False

    @staticmethod
    def set_assessment_flag(analysis_id: str, enabled: bool) -> bool:
        """Toggle EcosystemAnalysis.use_indicator_multipliers."""
        try:
            with get_db() as db:
                row = db.query(EcosystemAnalysis).filter(
                    EcosystemAnalysis.id == analysis_id
                ).first()
                if not row:
                    return False
                row.use_indicator_multipliers = bool(enabled)
                db.commit()
                return True
        except Exception as e:
            logger.error(f"set_assessment_flag failed: {e}")
            return False

    @staticmethod
    def get_responses(analysis_id: str) -> List[Dict]:
        """Return all response rows for an analysis, joined with indicator slug."""
        try:
            with get_db() as db:
                rows = (
                    db.query(AnalysisResponse, Indicator)
                    .join(Indicator, AnalysisResponse.indicator_id == Indicator.id)
                    .filter(AnalysisResponse.analysis_id == analysis_id)
                    .all()
                )
                out = []
                for r, ind in rows:
                    out.append({
                        'id': str(r.id),
                        'indicator_slug': ind.slug,
                        'indicator_code': ind.code,
                        'project_type_id': str(r.project_type_id) if r.project_type_id else None,
                        'is_committed': bool(r.is_committed),
                        'is_mandatory': bool(ind.is_mandatory),
                        'baseline_band_id': str(r.baseline_band_id) if r.baseline_band_id else None,
                        'baseline_score': float(r.baseline_score) if r.baseline_score is not None else None,
                        'baseline_year': r.baseline_year,
                        'target_band_id': str(r.target_band_id) if r.target_band_id else None,
                        'target_score': float(r.target_score) if r.target_score is not None else None,
                        'target_year': r.target_year,
                        'custom_score': float(r.custom_score) if r.custom_score is not None else None,
                        # Convenience: effective response score (0.0–1.0), preferring custom
                        'effective_score': (
                            float(r.custom_score) if r.custom_score is not None
                            else (float(r.baseline_score) if r.baseline_score is not None else None)
                        ),
                        'service_weights': ind.service_weights or {},
                        'applies_to_ecosystem': r.applies_to_ecosystem,
                        'followup_responses': r.followup_responses,
                        'notes': r.notes,
                    })
                return out
        except Exception as e:
            logger.error(f"get_responses failed: {e}")
            return []


class ComputedSubServiceMultiplierDB:
    """DAO for the materialised computed_sub_service_multipliers table.
    Rows are produced by utils.indicator_multipliers.compute_sub_service_multipliers
    and read by the results-page sub-service breakdown panel and the calc
    orchestrator (to build the {calc_key: final_multiplier} dict)."""

    @staticmethod
    def get_for_analysis(analysis_id: str) -> List[Dict]:
        """Return all computed rows for an analysis, keyed by sub-service."""
        try:
            with get_db() as db:
                rows = (
                    db.query(ComputedSubServiceMultiplier)
                    .filter(ComputedSubServiceMultiplier.analysis_id == analysis_id)
                    .all()
                )
                return [
                    {
                        'computation_id': str(r.computation_id),
                        'analysis_id': str(r.analysis_id),
                        'teeb_sub_service_key': r.teeb_sub_service_key,
                        'indicator_multiplier': r.indicator_multiplier,
                        'contributing_indicators': r.contributing_indicators or [],
                        'contributing_response_pcts': r.contributing_response_pcts or [],
                        'contributing_weights': r.contributing_weights or [],
                        'hd_multiplier': r.hd_multiplier,
                        'final_multiplier': r.final_multiplier,
                        'fallback_to_bbi': bool(r.fallback_to_bbi),
                        'bbi_value_used': r.bbi_value_used,
                        'computed_at': r.computed_at.isoformat() if r.computed_at else None,
                    }
                    for r in rows
                ]
        except Exception as e:
            logger.error(f"ComputedSubServiceMultiplierDB.get_for_analysis failed: {e}")
            return []

    @staticmethod
    def replace_for_analysis(analysis_id: str, rows: List[Dict]) -> bool:
        """Delete existing rows for this analysis and bulk-insert the new ones
        in a single transaction. Each row dict must contain the same keys as
        get_for_analysis (excluding computation_id and computed_at, which are
        assigned here)."""
        try:
            with get_db() as db:
                db.query(ComputedSubServiceMultiplier).filter(
                    ComputedSubServiceMultiplier.analysis_id == analysis_id
                ).delete(synchronize_session=False)
                for r in rows:
                    db.add(ComputedSubServiceMultiplier(
                        analysis_id=analysis_id,
                        teeb_sub_service_key=r['teeb_sub_service_key'],
                        indicator_multiplier=r.get('indicator_multiplier'),
                        contributing_indicators=r.get('contributing_indicators') or [],
                        contributing_response_pcts=r.get('contributing_response_pcts') or [],
                        contributing_weights=r.get('contributing_weights') or [],
                        hd_multiplier=r.get('hd_multiplier', 1.0),
                        final_multiplier=r['final_multiplier'],
                        fallback_to_bbi=bool(r.get('fallback_to_bbi', False)),
                        bbi_value_used=r.get('bbi_value_used'),
                    ))
                db.commit()
                return True
        except Exception as e:
            logger.error(f"ComputedSubServiceMultiplierDB.replace_for_analysis failed: {e}")
            return False


# Initialize user session
def initialize_user_session():
    """Initialize user session ID for database tracking"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    return st.session_state.user_id