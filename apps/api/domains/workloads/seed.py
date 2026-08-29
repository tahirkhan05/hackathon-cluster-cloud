"""Seed workload types into the database."""
from sqlalchemy.orm import Session

from domains.workloads.models import WorkloadType


def seed_workload_types(db: Session):
    """
    Seed initial workload types.
    
    MVP: Frame rendering workload type.
    """
    existing = db.query(WorkloadType).filter(
        WorkloadType.workload_type == "frame_rendering"
    ).first()
    
    if existing:
        print("Workload types already seeded")
        return
    
    frame_rendering = WorkloadType(
        workload_type="frame_rendering",
        name="3D Frame Rendering",
        parallelizable=True,
        description="Distributed rendering of 3D animation frames. Each frame is independent and can be rendered in parallel.",
        resource_requirements={
            "cpu_cores": 2,
            "ram_gb": 4,
            "gpu_required": False,  # Preferred but not required
            "gpu_model": "any",
            "docker_support": True
        },
        estimated_task_duration=60
    )
    
    db.add(frame_rendering)
    db.commit()
    
    print("✅ Workload types seeded successfully")
