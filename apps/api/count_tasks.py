#!/usr/bin/env python
"""Count tasks in database."""
from database import SessionLocal, engine
from sqlalchemy import text

db = SessionLocal()
try:
    # Count tasks directly with SQL
    result = db.execute(text("SELECT COUNT(*) FROM tasks"))
    total = result.scalar()
    print(f"Total tasks: {total}")
    
    # Get status breakdown
    result = db.execute(text("SELECT status, COUNT(*) FROM tasks GROUP BY status"))
    for row in result:
        print(f"  {row[0]}: {row[1]}")
    
    # Show sample tasks
    result = db.execute(text("SELECT task_id, job_id, status, node_id FROM tasks LIMIT 5"))
    rows = result.fetchall()
    if rows:
        print("\nSample tasks:")
        for row in rows:
            task_id, job_id, status, node_id = row
            print(f"  {task_id[:8] if task_id else 'N/A'}: job={job_id[:8] if job_id else 'N/A'}, status={status}, node={node_id or 'unassigned'}")
finally:
    db.close()
