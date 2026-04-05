#!/usr/bin/env python3
"""
Database migration script
"""
import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from app.core.config import settings
from app.core.database import Base
from app.models import Task, Property, PriceHistory, AgentExecution, Event, TaskSnapshot

def run_migrations():
    """Run database migrations"""
    print("Starting database migrations...")
    
    # Create sync engine
    engine = create_engine(
        settings.DATABASE_URL.replace('sqlite+aiosqlite:///', 'sqlite:///'),
        echo=True
    )
    
    try:
        # Create all tables
        Base.metadata.create_all(engine)
        
        print("Database migrations completed successfully!")
        print("Created tables:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")
            
    except Exception as e:
        print(f"Error during migrations: {e}")
    finally:
        engine.dispose()

if __name__ == "__main__":
    run_migrations()
