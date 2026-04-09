from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    weight_unit = Column(String, default="lbs", nullable=False, server_default="lbs")  # SET-01

    programs = relationship("Program", back_populates="owner")
    logs = relationship("WorkoutLog", back_populates="user")
    custom_exercises = relationship("Exercise", back_populates="creator")


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(String, primary_key=True)  # e.g. "e_bench_press" or "custom_123"
    name = Column(String, nullable=False, index=True)
    primary_muscle = Column(String, nullable=False, index=True)
    secondary_muscles = Column(JSON, default=[])
    category = Column(String, nullable=False)   # compound | isolation | cardio
    equipment = Column(String, nullable=False)  # barbell | dumbbell | machine | cable | bodyweight | plate
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # null = global built-in
    is_custom = Column(Boolean, default=False)

    creator = relationship("User", back_populates="custom_exercises")


# ── COM-01: Community Shared Exercises ───────────────────────────────────────

class SharedExercise(Base):
    __tablename__ = "shared_exercises"

    id = Column(Integer, primary_key=True, index=True)
    submitted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False, index=True)
    primary_muscle = Column(String, nullable=False, index=True)
    secondary_muscles = Column(JSON, default=[])
    equipment = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text, nullable=True)               # optional cue / notes, max 300 chars
    status = Column(String, default="pending", nullable=False, index=True)  # pending | approved | rejected
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    use_count = Column(Integer, default=0, nullable=False)

    submitter = relationship("User", foreign_keys=[submitted_by_user_id])


class Program(Base):
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    template_key = Column(String, nullable=True)   # "ppl", "upperlower", etc.
    days = Column(JSON, nullable=False)            # full JSONB day/group/exercise structure
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="programs")
    logs = relationship("WorkoutLog", back_populates="program")


class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True)
    day_label = Column(String)       # "MON", "TUE", etc.
    day_type = Column(String)        # "push", "pull", "legs", etc.
    day_title = Column(String)       # "PUSH A"
    exercises = Column(JSON)         # [{name, weight, note, isPR}]
    logged_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="logs")
    program = relationship("Program", back_populates="logs")


class UserProgress(Base):
    """Queue-based rolling pointer — tracks which workout is 'Next Up'."""
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True)
    last_completed_index = Column(Integer, default=-1, nullable=False)  # -1 = nothing done yet
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User")


class PersonalRecord(Base):
    __tablename__ = "personal_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_name = Column(String, nullable=False, index=True)
    weight = Column(Float, nullable=False)
    display = Column(String)         # "135 × 8"
    set_at = Column(DateTime(timezone=True), server_default=func.now())