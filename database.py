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
    sustainability_responses = Column(JSON, nullable=True)  # Store sustainability assessment responses
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

class NaturalCapitalBaseline(Base):
    """Store baseline natural capital values for ecosystem tracking"""
    __tablename__ = "natural_capital_baselines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    area_id = Column(UUID(as_uuid=True), nullable=True)  # Reference to SavedArea
    user_session_id = Column(String(255), nullable=True)
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
        # Test connection first
        with engine.connect() as connection:
            pass
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        return True
    except Exception as e:
        import traceback
        error_msg = f"Database initialization failed: {str(e)}"
        if 'st' in globals():
            st.error(error_msg)
            st.error(f"Details: {traceback.format_exc()}")
        else:
            print(error_msg)
            print(f"Details: {traceback.format_exc()}")
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
        db = None
        try:
            db = get_db()
            
            # Handle session state safely
            session_user_id = None
            try:
                if hasattr(st, 'session_state') and 'user_id' in st.session_state:
                    session_user_id = st.session_state.get('user_id')
            except:
                pass  # No session state available
            
            analysis = EcosystemAnalysis(
                user_session_id=user_session_id or session_user_id,
                area_name=area_name,
                coordinates=coordinates,
                area_hectares=area_hectares,
                ecosystem_type=ecosystem_type,
                total_value=total_value,
                value_per_hectare=value_per_hectare,
                analysis_results=analysis_results,
                sustainability_responses=sustainability_responses,
                sampling_points=sampling_points,
                data_source=analysis_results.get('data_source', 'ESVD/TEEB Database')
            )
            
            db.add(analysis)
            db.commit()
            db.refresh(analysis)
            
            analysis_id = str(analysis.id)
            return analysis_id
            
        except Exception as e:
            error_msg = f"Failed to save analysis: {str(e)}"
            import traceback
            traceback_msg = f"Traceback: {traceback.format_exc()}"
            
            # Try to show error in Streamlit if available
            try:
                if hasattr(st, 'error'):
                    st.error(error_msg)
                    st.error(traceback_msg)
            except:
                # Fallback to print if no Streamlit context
                print(error_msg)
                print(traceback_msg)
            
            return None
        finally:
            if db:
                db.close()
    
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
            import traceback
            st.error(f"Traceback: {traceback.format_exc()}")
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
            db = get_db()
            
            # Extract service values from analysis results
            esvd_data = analysis_results.get('esvd_results', {})
            provisioning = esvd_data.get('provisioning', {}).get('total', 0)
            regulating = esvd_data.get('regulating', {}).get('total', 0)
            cultural = esvd_data.get('cultural', {}).get('total', 0)
            supporting = esvd_data.get('supporting', {}).get('total', 0)
            
            # Calculate environmental indicators if available
            detected_ecosystem = st.session_state.get('detected_ecosystem', {})
            vegetation_health = detected_ecosystem.get('confidence', 0.5)
            biodiversity_index = 0
            
            # Calculate biodiversity if multiple ecosystems detected
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
            
            baseline_id = str(baseline.id)
            db.close()
            return baseline_id
            
        except Exception as e:
            st.error(f"Failed to create baseline: {str(e)}")
            return None
    
    @staticmethod
    def get_area_baseline(area_id: str) -> Optional[Dict]:
        """Get the most recent baseline for an area"""
        try:
            db = get_db()
            
            baseline = db.query(NaturalCapitalBaseline).filter(
                NaturalCapitalBaseline.area_id == area_id
            ).order_by(NaturalCapitalBaseline.baseline_date.desc()).first()
            
            if baseline:
                result = {
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
                    'data_quality_score': baseline.data_quality_score
                }
                db.close()
                return result
            
            db.close()
            return None
            
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
            db = get_db()
            
            baseline = db.query(NaturalCapitalBaseline).filter(
                NaturalCapitalBaseline.id == baseline_id
            ).first()
            
            if baseline is None:
                return None
            
            # Calculate changes
            baseline_value = float(baseline.total_baseline_value) if baseline.total_baseline_value is not None else 0.0
            total_change = current_analysis['total_value'] - baseline_value
            percent_change = (total_change / baseline_value) * 100 if baseline_value > 0 else 0
            
            # Determine trend direction
            if abs(percent_change) < 5:
                trend_direction = 'stable'
            elif percent_change > 0:
                trend_direction = 'improving'
            else:
                trend_direction = 'declining'
            
            # Extract current service values
            esvd_data = current_analysis.get('esvd_results', {})
            current_provisioning = esvd_data.get('provisioning', {}).get('total', 0)
            current_regulating = esvd_data.get('regulating', {}).get('total', 0)
            current_cultural = esvd_data.get('cultural', {}).get('total', 0)
            current_supporting = esvd_data.get('supporting', {}).get('total', 0)
            
            provisioning_change = current_provisioning - (baseline.provisioning_baseline if baseline.provisioning_baseline is not None else 0.0)
            regulating_change = current_regulating - (baseline.regulating_baseline if baseline.regulating_baseline is not None else 0.0)
            cultural_change = current_cultural - (baseline.cultural_baseline if baseline.cultural_baseline is not None else 0.0)
            supporting_change = current_supporting - (baseline.supporting_baseline if baseline.supporting_baseline is not None else 0.0)
            
            # Create trend record
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
            
            # Return comparison results
            result = {
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
                    'supporting': supporting_change
                },
                'baseline_values': {
                    'total': baseline.total_baseline_value,
                    'provisioning': baseline.provisioning_baseline,
                    'regulating': baseline.regulating_baseline,
                    'cultural': baseline.cultural_baseline,
                    'supporting': baseline.supporting_baseline
                }
            }
            
            db.close()
            return result
            
        except Exception as e:
            st.error(f"Failed to compare to baseline: {str(e)}")
            return None

# Initialize user session
def initialize_user_session():
    """Initialize user session ID for database tracking"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    return st.session_state.user_id