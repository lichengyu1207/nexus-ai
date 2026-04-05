from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task, TaskStep
from app.schemas.task import TaskCreate, TaskUpdate, TaskStepCreate


class TaskManager:
    """Manages the lifecycle of analysis tasks"""
    
    @staticmethod
    async def create_task(db: AsyncSession, task_data: TaskCreate) -> Task:
        """Create a new analysis task"""
        db_task = Task(
            id=str(datetime.utcnow().timestamp()),  # Simple ID generation
            property_id=task_data.property_id,
            status="pending",
            progress=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)
        
        # Create initial task steps
        for step_data in task_data.steps:
            db_step = TaskStep(
                id=str(datetime.utcnow().timestamp() + len(task_data.steps)),  # Simple ID generation
                task_id=db_task.id,
                name=step_data.name,
                description=step_data.description,
                status="pending",
                progress=0,
                created_at=datetime.utcnow()
            )
            db.add(db_step)
        
        await db.commit()
        return db_task
    
    @staticmethod
    async def get_task(db: AsyncSession, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        from sqlalchemy import select
        result = await db.execute(select(Task).where(Task.id == task_id))
        return result.scalars().first()
    
    @staticmethod
    async def update_task_status(db: AsyncSession, task_id: str, status: str, progress: int) -> Task:
        """Update task status and progress"""
        task = await TaskManager.get_task(db, task_id)
        if task:
            task.status = status
            task.progress = progress
            task.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(task)
        return task
    
    @staticmethod
    async def update_step_status(
        db: AsyncSession, 
        step_id: str, 
        status: str, 
        progress: int,
        result: Optional[str] = None,
        error: Optional[str] = None
    ) -> TaskStep:
        """Update task step status and progress"""
        from sqlalchemy import select
        result_query = await db.execute(select(TaskStep).where(TaskStep.id == step_id))
        step = result_query.scalars().first()
        
        if step:
            step.status = status
            step.progress = progress
            step.result = result
            step.error = error
            step.updated_at = datetime.utcnow()
            
            if status == "completed":
                step.completed_at = datetime.utcnow()
            elif status == "processing" and not step.started_at:
                step.started_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(step)
        
        return step