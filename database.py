"""
Database configuration and models for Ecosystem Valuation Engine
"""

import os
import uuid
import logging
from datetime import datetime
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_users_email', 'email'),
    )


class EcosystemAnalysis(Base):
    """Store ecosystem analysis results"""
    __tablename__ = "ecosystem_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_session_id = Column(String(255), nullable=True)  # For tracking user sessions
    user_account_id = Column(UUID(as_uuid=True), nullable=True)  # Registered user FK
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
    def register(email: str, password: str, display_name: Optional[str] = None) -> Dict:
        """Hash password and create a new user. Raises ValueError on duplicate email."""
        import bcrypt
        try:
            with get_db() as db:
                existing = db.query(User).filter(User.email == email.lower()).first()
                if existing:
                    raise ValueError("An account with that email address already exists.")
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                user = User(
                    email=email.lower(),
                    password_hash=password_hash,
                    display_name=display_name,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                return {'id': str(user.id), 'email': user.email, 'display_name': user.display_name}
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            raise

    @staticmethod
    def login(email: str, password: str) -> Optional[Dict]:
        """Verify credentials and return user dict, or None on failure."""
        import bcrypt
        try:
            with get_db() as db:
                user = db.query(User).filter(User.email == email.lower()).first()
                if not user:
                    return None
                if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                    return {'id': str(user.id), 'email': user.email, 'display_name': user.display_name}
                return None
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return None

    @staticmethod
    def get_by_id(user_id: str) -> Optional[Dict]:
        """Return user dict by UUID string, or None."""
        try:
            with get_db() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return None
                return {'id': str(user.id), 'email': user.email, 'display_name': user.display_name}
        except Exception as e:
            logger.error(f"get_by_id failed: {e}")
            return None


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
        sustainability_responses: Optional[Dict[str, Any]] = None
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

                clean_coordinates = convert_numpy_types(coordinates)
                clean_analysis_results = convert_numpy_types(analysis_results)
                clean_sustainability_responses = convert_numpy_types(sustainability_responses) if sustainability_responses else None
                clean_area_hectares = float(area_hectares) if isinstance(area_hectares, np.floating) else area_hectares
                clean_total_value = float(total_value) if isinstance(total_value, np.floating) else total_value
                clean_value_per_hectare = float(value_per_hectare) if isinstance(value_per_hectare, np.floating) else value_per_hectare

                analysis = EcosystemAnalysis(
                    user_session_id=user_session_id or session_user_id,
                    user_account_id=auth_user_id,
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
        user_session_id: Optional[str] = None
    ) -> Optional[str]:
        """Save area for future analysis"""
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

# Initialize user session
def initialize_user_session():
    """Initialize user session ID for database tracking"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    return st.session_state.user_id