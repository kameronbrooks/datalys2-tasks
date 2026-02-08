from sqlalchemy import create_engine, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from datetime import datetime
from typing import Optional
from ..core.config import settings

class Base(DeclarativeBase):
    pass

class ScheduledTaskDB(Base):
    __tablename__ = "scheduled_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_name: Mapped[str] = mapped_column(String, unique=True, index=True)
    script_path: Mapped[str] = mapped_column(String)
    schedule_type: Mapped[str] = mapped_column(String) # DAILY, HOURLY, etc.
    schedule_time: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    interval_minutes: Mapped[Optional[int]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
