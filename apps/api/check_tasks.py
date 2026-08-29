from database import SessionLocal
from domains.tasks.models import Task

db = SessionLocal()
tasks = db.query(Task).all()
print(f"Total tasks: {len(tasks)}")
for t in tasks[:10]:
    print(f"Task {t.task_id}: job={t.job_id}, status={t.status}")
db.close()
