"""Initialize database with tables and seed data."""
import sys
from database import engine, Base, SessionLocal
from domains.workloads.seed import seed_workload_types

# Import all models to ensure they're registered
from domains.jobs.models import Job
from domains.tasks.models import Task
from domains.nodes.models import Node
from domains.incidents.models import Incident
from domains.reliability.models import ReliabilityScore
from domains.ledger.models import Transaction
from domains.workloads.models import WorkloadType


def init_database():
    """Initialize database schema and seed data."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully")
    
    # Seed initial data
    db = SessionLocal()
    try:
        seed_workload_types(db)
    finally:
        db.close()
    
    print("✅ Database initialized successfully")


if __name__ == "__main__":
    init_database()
