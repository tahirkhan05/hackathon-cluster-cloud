"""Initialize database with tables and seed data."""
from database import SessionLocal
from domains.workloads.seed import seed_workload_types


def init_database():
    """Seed initial data."""
    db = SessionLocal()
    try:
        seed_workload_types(db)
    except Exception as e:
        print(f"Seed warning: {e}")
    finally:
        db.close()
