"""
Database configuration and models for Ecosystem Valuation Engine
"""

import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import psycopg2
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
import streamlit as st

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class EcosystemAnalysis(Base):
    """Store ecosystem analysis results"""
    __tablename__ = "ecosystem_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_session_id = Column(String(255), nullable=True)  # For tracking user sessions
    area_name = Column(String(255), nullable=True)
    coordinates = Column(JSON, nullable=False)  # Store GeoJSON coordinates
    area_hectares = Column(Float, nullable=False)
    ecosystem_type = Column(String(255), nullable=False)
    total_value = Column(Float, nullable=False)
    value_per_hectare = Column(Float, nullable=False)
    analysis_results = Column(JSON, nullable=False)  # Store full analysis data
    sampling_points = Column(Integer, nullable=False, default=10)
    data_source = Column(String(255), nullable=False, default='ESVD')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SavedArea(Base):
    """Store user-saved areas for future analysis"""
    __tablename__ = "saved_areas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_session_id = Column(String(255), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    coordinates = Column(JSON, nullable=False)
    area_hectares = Column(Float, nullable=False)
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

# Database utility functions
def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise e

def init_database():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        return True
    except Exception as e:
        st.error(f"Database initialization failed: {str(e)}")
        return False

def test_database_connection():
    """Test database connection"""
    try:
        with engine.connect() as connection:
            from sqlalchemy import text
            result = connection.execute(text("SELECT 1"))
            return True
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        return False

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
        user_session_id: Optional[str] = None
    ) -> Optional[str]:
        """Save ecosystem analysis to database"""
        try:
            db = get_db()
            
            analysis = EcosystemAnalysis(
                user_session_id=user_session_id or st.session_state.get('user_id'),
                area_name=area_name,
                coordinates=coordinates,
                area_hectares=area_hectares,
                ecosystem_type=ecosystem_type,
                total_value=total_value,
                value_per_hectare=value_per_hectare,
                analysis_results=analysis_results,
                sampling_points=sampling_points
            )
            
            db.add(analysis)
            db.commit()
            db.refresh(analysis)
            
            analysis_id = str(analysis.id)
            db.close()
            return analysis_id
            
        except Exception as e:
            st.error(f"Failed to save analysis: {str(e)}")
            return None
    
    @staticmethod
    def get_user_analyses(user_session_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get user's recent analyses"""
        try:
            db = get_db()
            session_id = user_session_id or st.session_state.get('user_id')
            
            analyses = db.query(EcosystemAnalysis).filter(
                EcosystemAnalysis.user_session_id == session_id
            ).order_by(EcosystemAnalysis.created_at.desc()).limit(limit).all()
            
            result = []
            for analysis in analyses:
                result.append({
                    'id': str(analysis.id),
                    'area_name': analysis.area_name,
                    'ecosystem_type': analysis.ecosystem_type,
                    'total_value': analysis.total_value,
                    'area_hectares': analysis.area_hectares,
                    'created_at': analysis.created_at,
                    'coordinates': analysis.coordinates
                })
            
            db.close()
            return result
            
        except Exception as e:
            st.error(f"Failed to retrieve analyses: {str(e)}")
            return []
    
    @staticmethod
    def get_analysis_by_id(analysis_id: str) -> Optional[Dict]:
        """Get specific analysis by ID"""
        try:
            db = get_db()
            
            analysis = db.query(EcosystemAnalysis).filter(
                EcosystemAnalysis.id == analysis_id
            ).first()
            
            if analysis:
                result = {
                    'id': str(analysis.id),
                    'area_name': analysis.area_name,
                    'coordinates': analysis.coordinates,
                    'area_hectares': analysis.area_hectares,
                    'ecosystem_type': analysis.ecosystem_type,
                    'total_value': analysis.total_value,
                    'value_per_hectare': analysis.value_per_hectare,
                    'analysis_results': analysis.analysis_results,
                    'sampling_points': analysis.sampling_points,
                    'created_at': analysis.created_at
                }
                db.close()
                return result
            
            db.close()
            return None
            
        except Exception as e:
            st.error(f"Failed to retrieve analysis: {str(e)}")
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
            db = get_db()
            
            saved_area = SavedArea(
                user_session_id=user_session_id or st.session_state.get('user_id'),
                name=name,
                description=description,
                coordinates=coordinates,
                area_hectares=area_hectares
            )
            
            db.add(saved_area)
            db.commit()
            db.refresh(saved_area)
            
            area_id = str(saved_area.id)
            db.close()
            return area_id
            
        except Exception as e:
            st.error(f"Failed to save area: {str(e)}")
            return None
    
    @staticmethod
    def get_user_saved_areas(user_session_id: Optional[str] = None) -> List[Dict]:
        """Get user's saved areas"""
        try:
            db = get_db()
            session_id = user_session_id or st.session_state.get('user_id')
            
            areas = db.query(SavedArea).filter(
                SavedArea.user_session_id == session_id
            ).order_by(SavedArea.updated_at.desc()).all()
            
            result = []
            for area in areas:
                result.append({
                    'id': str(area.id),
                    'name': area.name,
                    'description': area.description,
                    'coordinates': area.coordinates,
                    'area_hectares': area.area_hectares,
                    'is_favorite': area.is_favorite,
                    'created_at': area.created_at
                })
            
            db.close()
            return result
            
        except Exception as e:
            st.error(f"Failed to retrieve saved areas: {str(e)}")
            return []

# Initialize user session
def initialize_user_session():
    """Initialize user session ID for database tracking"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    return st.session_state.user_id