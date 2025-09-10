"""
Database Connection
SQLAlchemy database connection and table creation utilities
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_database_url():
    """
    Get database URL from environment or default to PostgreSQL
    """
    # Check for environment variable first
    db_url = os.getenv('DATABASE_URL')
    
    if db_url:
        return db_url
    
    # Default PostgreSQL configuration
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    database = os.getenv('DB_NAME', 'agentic_studio')
    username = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', 'password')
    
    return f"postgresql://{username}:{password}@{host}:{port}/{database}"


def create_tables():
    """
    Create all database tables using SQLAlchemy models
    """
    from src.models.tenant import Base
    
    # Get database URL
    database_url = get_database_url()
    
    # Create engine
    engine = create_engine(database_url)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    return True


def get_session_factory():
    """
    Get SQLAlchemy session factory
    """
    database_url = get_database_url()
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal


def get_db_session():
    """
    Get database session (dependency injection helper)
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()