from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import os, models, auth
from database import engine, get_db, seed_exercises, DATABASE_URL, SessionLocal

models.Base.metadata.create_all(bind=engine)

# Auto-migrate: add missing columns on every deploy
from sqlalchemy import text, inspect as sa_inspect

def run_migrations(engine):
    with engine.connect() as conn:
        inspector = sa_inspect(engine)
        cols = [c['name'] for c in inspector.get_columns('users')]
        if 'weight_unit' not in cols:
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN weight_unit VARCHAR NOT NULL DEFAULT 'lbs'"
            ))
            conn.commit()
        # Queue-based progress table migration
        existing_tables = inspector.get_table_names()
        if 'user_progress' not in existing_tables:
            is_pg = DATABASE_URL.startswith("postgresql")
            id_col = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
            ts_col = "TIMESTAMP WITH TIME ZONE DEFAULT NOW()" if is_pg else "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            conn.execute(text(f"""
                CREATE TABLE user_progress (
                    id {id_col},
                    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
                    program_id INTEGER REFERENCES programs(id),
                    last_completed_index INTEGER NOT NULL DEFAULT -1,
                    updated_at {ts_col}
                )
            """))
            conn.commit()

run_migrations(engine)

# FIX: get_db() is a generator (yields), not a context manager — use SessionLocal directly for startup
_startup_db = SessionLocal()
try:
    seed_exercises(_startup_db)
finally:
    _startup_db.close()

app = FastAPI(title="My Split API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str

class ExerciseOut(BaseModel):
    id: str
    name: str
    primary_muscle: str
    secondary_muscles: List[str]
    category: str
    equipment: str
    is_custom: bool

class CustomExerciseRequest(BaseModel):
    name: str
    primary_muscle: str
    secondary_muscles: List[str] = []
    category: str
    equipment: str

class ProgramRequest(BaseModel):
    name: str
    template_key: Optional[str] = None
    days: list

class ProgramOut(BaseModel):
    id: int
    name: str
    template_key: Optional[str]
    days: list
    is_active: bool

class LogRequest(BaseModel):
    program_id: Optional[int] = None
    day_label: str
    day_type: str
    day_title: str
    exercises: list

class LogOut(BaseModel):
    id: int
    day_label: str
    day_type: str
    day_title: str
    exercises: list
    logged_at: str

class PRRequest(BaseModel):
    exercise_name: str
    weight: float
    display: str

class PROut(BaseModel):
    exercise_name: str
    weight: float
    display: str
    set_at: str

class WeightUnitRequest(BaseModel):
    weight_unit: str  # "lbs" | "kg"

class SharedExerciseRequest(BaseModel):
    name: str
    primary_muscle: str
    secondary_muscles: List[str] = []
    equipment: str
    category: str
    description: Optional[str] = None

class SharedExerciseOut(BaseModel):
    id: int
    name: str
    primary_muscle: str
    secondary_muscles: List[str]
    equipment: str
    category: str
    description: Optional[str]
    status: str
    use_count: int
    submitted_at: str
    submitter_username: Optional[str] = None


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.post("/api/auth/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == req.email).first():
        raise HTTPException(400, "Email already registered")
    if db.query(models.User).filter(models.User.username == req.username).first():
        raise HTTPException(400, "Username already taken")
    user = models.User(email=req.email, username=req.username,
                       hashed_password=auth.hash_password(req.password))
    db.add(user); db.commit(); db.refresh(user)
    return TokenResponse(access_token=auth.create_access_token(user.id),
                         user_id=user.id, username=user.username)

@app.post("/api/auth/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = (db.query(models.User).filter(models.User.email == form.username).first() or
            db.query(models.User).filter(models.User.username == form.username).first())
    if not user or not auth.verify_password(form.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    return TokenResponse(access_token=auth.create_access_token(user.id),
                         user_id=user.id, username=user.username)

@app.get("/api/auth/me")
def me(current_user: models.User = Depends(auth.get_current_user)):
    return {"id": current_user.id, "username": current_user.username, "email": current_user.email}


# ── Exercises ─────────────────────────────────────────────────────────────────

@app.get("/api/exercises", response_model=List[ExerciseOut])
def get_exercises(muscle: Optional[str] = None,
                  current_user: models.User = Depends(auth.get_current_user),
                  db: Session = Depends(get_db)):
    q = db.query(models.Exercise).filter(
        (models.Exercise.user_id == None) | (models.Exercise.user_id == current_user.id))
    if muscle and muscle != "all":
        q = q.filter(models.Exercise.primary_muscle == muscle)
    return q.order_by(models.Exercise.name).all()

@app.post("/api/exercises", response_model=ExerciseOut, status_code=201)
def create_exercise(req: CustomExerciseRequest,
                    current_user: models.User = Depends(auth.get_current_user),
                    db: Session = Depends(get_db)):
    ex_id = f"custom_{current_user.id}_{int(__import__('time').time())}"
    ex = models.Exercise(id=ex_id, name=req.name, primary_muscle=req.primary_muscle,
                         secondary_muscles=req.secondary_muscles, category=req.category,
                         equipment=req.equipment, user_id=current_user.id, is_custom=True)
    db.add(ex); db.commit(); db.refresh(ex)
    return ex

@app.delete("/api/exercises/{exercise_id}", status_code=204)
def delete_exercise(exercise_id: str,
                    current_user: models.User = Depends(auth.get_current_user),
                    db: Session = Depends(get_db)):
    ex = db.query(models.Exercise).filter(
        models.Exercise.id == exercise_id,
        models.Exercise.user_id == current_user.id).first()
    if not ex:
        raise HTTPException(404, "Exercise not found or not yours")
    db.delete(ex); db.commit()


# ── Programs ──────────────────────────────────────────────────────────────────

@app.get("/api/programs", response_model=List[ProgramOut])
def get_programs(current_user: models.User = Depends(auth.get_current_user),
                 db: Session = Depends(get_db)):
    return db.query(models.Program).filter(models.Program.user_id == current_user.id).all()

@app.post("/api/programs", response_model=ProgramOut, status_code=201)
def create_program(req: ProgramRequest,
                   current_user: models.User = Depends(auth.get_current_user),
                   db: Session = Depends(get_db)):
    prog = models.Program(user_id=current_user.id, name=req.name,
                          template_key=req.template_key, days=req.days)
    db.add(prog); db.commit(); db.refresh(prog)
    return prog

@app.put("/api/programs/{program_id}", response_model=ProgramOut)
def update_program(program_id: int, req: ProgramRequest,
                   current_user: models.User = Depends(auth.get_current_user),
                   db: Session = Depends(get_db)):
    prog = db.query(models.Program).filter(
        models.Program.id == program_id,
        models.Program.user_id == current_user.id).first()
    if not prog:
        raise HTTPException(404, "Program not found")
    prog.name = req.name; prog.days = req.days; prog.template_key = req.template_key
    db.commit(); db.refresh(prog)
    return prog

@app.delete("/api/programs/{program_id}", status_code=204)
def delete_program(program_id: int,
                   current_user: models.User = Depends(auth.get_current_user),
                   db: Session = Depends(get_db)):
    prog = db.query(models.Program).filter(
        models.Program.id == program_id,
        models.Program.user_id == current_user.id).first()
    if not prog:
        raise HTTPException(404, "Program not found")
    db.delete(prog); db.commit()


# ── Logs ──────────────────────────────────────────────────────────────────────

@app.get("/api/logs", response_model=List[LogOut])
def get_logs(limit: int = 50,
             current_user: models.User = Depends(auth.get_current_user),
             db: Session = Depends(get_db)):
    rows = (db.query(models.WorkoutLog)
            .filter(models.WorkoutLog.user_id == current_user.id)
            .order_by(models.WorkoutLog.logged_at.desc())
            .limit(limit).all())
    return [LogOut(id=r.id, day_label=r.day_label, day_type=r.day_type,
                   day_title=r.day_title, exercises=r.exercises,
                   logged_at=r.logged_at.isoformat()) for r in rows]

@app.post("/api/logs", response_model=LogOut, status_code=201)
def create_log(req: LogRequest,
               current_user: models.User = Depends(auth.get_current_user),
               db: Session = Depends(get_db)):
    log = models.WorkoutLog(user_id=current_user.id, program_id=req.program_id,
                            day_label=req.day_label, day_type=req.day_type,
                            day_title=req.day_title, exercises=req.exercises)
    db.add(log); db.commit(); db.refresh(log)
    return LogOut(id=log.id, day_label=log.day_label, day_type=log.day_type,
                  day_title=log.day_title, exercises=log.exercises,
                  logged_at=log.logged_at.isoformat())

@app.delete("/api/logs/{log_id}", status_code=204)
def delete_log(log_id: int,
               current_user: models.User = Depends(auth.get_current_user),
               db: Session = Depends(get_db)):
    log = db.query(models.WorkoutLog).filter(
        models.WorkoutLog.id == log_id,
        models.WorkoutLog.user_id == current_user.id).first()
    if not log:
        raise HTTPException(404, "Log not found")
    db.delete(log); db.commit()


# ── Personal Records ──────────────────────────────────────────────────────────

@app.get("/api/prs", response_model=List[PROut])
def get_prs(current_user: models.User = Depends(auth.get_current_user),
            db: Session = Depends(get_db)):
    rows = db.query(models.PersonalRecord).filter(
        models.PersonalRecord.user_id == current_user.id
    ).order_by(models.PersonalRecord.set_at.desc()).all()
    return [PROut(exercise_name=r.exercise_name, weight=r.weight,
                  display=r.display, set_at=r.set_at.isoformat()) for r in rows]

@app.post("/api/prs", response_model=PROut, status_code=201)
def upsert_pr(req: PRRequest,
              current_user: models.User = Depends(auth.get_current_user),
              db: Session = Depends(get_db)):
    existing = db.query(models.PersonalRecord).filter(
        models.PersonalRecord.user_id == current_user.id,
        models.PersonalRecord.exercise_name == req.exercise_name).first()
    if existing:
        if req.weight <= existing.weight:
            raise HTTPException(400, "Not a new PR")
        existing.weight = req.weight; existing.display = req.display
        db.commit(); db.refresh(existing)
        return PROut(exercise_name=existing.exercise_name, weight=existing.weight,
                     display=existing.display, set_at=existing.set_at.isoformat())
    pr = models.PersonalRecord(user_id=current_user.id, exercise_name=req.exercise_name,
                                weight=req.weight, display=req.display)
    db.add(pr); db.commit(); db.refresh(pr)
    return PROut(exercise_name=pr.exercise_name, weight=pr.weight,
                 display=pr.display, set_at=pr.set_at.isoformat())


# ── Queue Progress (Rolling Pointer) ─────────────────────────────────────────

class ProgressOut(BaseModel):
    last_completed_index: int
    program_id: Optional[int]

class AdvanceRequest(BaseModel):
    program_id: int
    completed_index: int

@app.get("/api/progress", response_model=ProgressOut)
def get_progress(current_user: models.User = Depends(auth.get_current_user),
                 db: Session = Depends(get_db)):
    prog = db.query(models.UserProgress).filter(
        models.UserProgress.user_id == current_user.id).first()
    if not prog:
        return ProgressOut(last_completed_index=-1, program_id=None)
    return ProgressOut(last_completed_index=prog.last_completed_index,
                       program_id=prog.program_id)

@app.post("/api/progress/advance", response_model=ProgressOut)
def advance_progress(req: AdvanceRequest,
                     current_user: models.User = Depends(auth.get_current_user),
                     db: Session = Depends(get_db)):
    prog = db.query(models.UserProgress).filter(
        models.UserProgress.user_id == current_user.id).first()
    if not prog:
        prog = models.UserProgress(user_id=current_user.id,
                                   program_id=req.program_id,
                                   last_completed_index=req.completed_index)
        db.add(prog)
    else:
        # FIX: if the user switched programs, reset the index to 0 instead of
        # carrying over a stale index from the old program
        if prog.program_id != req.program_id:
            prog.last_completed_index = req.completed_index
        else:
            prog.last_completed_index = req.completed_index
        prog.program_id = req.program_id
    db.commit(); db.refresh(prog)
    return ProgressOut(last_completed_index=prog.last_completed_index,
                       program_id=prog.program_id)

@app.post("/api/progress/reset", response_model=ProgressOut)
def reset_progress(current_user: models.User = Depends(auth.get_current_user),
                   db: Session = Depends(get_db)):
    prog = db.query(models.UserProgress).filter(
        models.UserProgress.user_id == current_user.id).first()
    if prog:
        prog.last_completed_index = -1
        db.commit(); db.refresh(prog)
        return ProgressOut(last_completed_index=-1, program_id=prog.program_id)
    return ProgressOut(last_completed_index=-1, program_id=None)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


# ── SET-01: Weight Unit Preference ────────────────────────────────────────────

@app.get("/api/auth/preferences")
def get_preferences(current_user: models.User = Depends(auth.get_current_user)):
    return {"weight_unit": current_user.weight_unit or "lbs"}

@app.put("/api/auth/preferences")
def update_preferences(req: WeightUnitRequest,
                        current_user: models.User = Depends(auth.get_current_user),
                        db: Session = Depends(get_db)):
    if req.weight_unit not in ("lbs", "kg"):
        raise HTTPException(400, "weight_unit must be 'lbs' or 'kg'")
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    user.weight_unit = req.weight_unit
    db.commit()
    return {"weight_unit": user.weight_unit}


# ── COM-02: Shared Exercise Routes ────────────────────────────────────────────

def _shared_out(ex: models.SharedExercise, db: Session) -> SharedExerciseOut:
    submitter = db.query(models.User).filter(models.User.id == ex.submitted_by_user_id).first()
    return SharedExerciseOut(
        id=ex.id, name=ex.name, primary_muscle=ex.primary_muscle,
        secondary_muscles=ex.secondary_muscles or [], equipment=ex.equipment,
        category=ex.category, description=ex.description, status=ex.status,
        use_count=ex.use_count,
        submitted_at=ex.submitted_at.isoformat(),
        submitter_username=submitter.username if submitter else None,
    )

@app.post("/api/shared-exercises", response_model=SharedExerciseOut, status_code=201)
def submit_shared_exercise(req: SharedExerciseRequest,
                            current_user: models.User = Depends(auth.get_current_user),
                            db: Session = Depends(get_db)):
    if req.description and len(req.description) > 300:
        raise HTTPException(400, "Description must be 300 chars or fewer")
    allowed_muscles = {"chest","back","shoulders","biceps","triceps","quads",
                        "hamstrings","glutes","calves","abs","forearms","traps","core"}
    if req.primary_muscle not in allowed_muscles:
        raise HTTPException(400, f"primary_muscle must be one of: {', '.join(sorted(allowed_muscles))}")
    ex = models.SharedExercise(
        submitted_by_user_id=current_user.id, name=req.name,
        primary_muscle=req.primary_muscle, secondary_muscles=req.secondary_muscles,
        equipment=req.equipment, category=req.category,
        description=req.description, status="pending",
    )
    db.add(ex); db.commit(); db.refresh(ex)
    return _shared_out(ex, db)

@app.get("/api/shared-exercises", response_model=List[SharedExerciseOut])
def list_shared_exercises(status: Optional[str] = "approved",
                           muscle: Optional[str] = None,
                           current_user: models.User = Depends(auth.get_current_user),
                           db: Session = Depends(get_db)):
    q = db.query(models.SharedExercise)
    if status == "approved":
        q = q.filter(models.SharedExercise.status == "approved")
    elif status == "mine":
        q = q.filter(models.SharedExercise.submitted_by_user_id == current_user.id)
    else:
        q = q.filter(
            (models.SharedExercise.submitted_by_user_id == current_user.id) |
            (models.SharedExercise.status == "approved")
        )
    if muscle and muscle != "all":
        q = q.filter(models.SharedExercise.primary_muscle == muscle)
    rows = q.order_by(models.SharedExercise.use_count.desc(), models.SharedExercise.name).all()
    return [_shared_out(r, db) for r in rows]

@app.get("/api/shared-exercises/pending", response_model=List[SharedExerciseOut])
def list_pending(current_user: models.User = Depends(auth.get_current_user),
                 db: Session = Depends(get_db)):
    if current_user.id != 1:
        raise HTTPException(403, "Admin only")
    rows = db.query(models.SharedExercise).filter(
        models.SharedExercise.status == "pending"
    ).order_by(models.SharedExercise.submitted_at).all()
    return [_shared_out(r, db) for r in rows]

@app.put("/api/shared-exercises/{exercise_id}/approve", response_model=SharedExerciseOut)
def approve_shared_exercise(exercise_id: int,
                              current_user: models.User = Depends(auth.get_current_user),
                              db: Session = Depends(get_db)):
    if current_user.id != 1:
        raise HTTPException(403, "Admin only")
    from datetime import datetime, timezone
    ex = db.query(models.SharedExercise).filter(models.SharedExercise.id == exercise_id).first()
    if not ex:
        raise HTTPException(404, "Exercise not found")
    ex.status = "approved"
    ex.approved_by = current_user.id
    ex.approved_at = datetime.now(timezone.utc)
    db.commit(); db.refresh(ex)
    return _shared_out(ex, db)

@app.put("/api/shared-exercises/{exercise_id}/reject", response_model=SharedExerciseOut)
def reject_shared_exercise(exercise_id: int,
                             current_user: models.User = Depends(auth.get_current_user),
                             db: Session = Depends(get_db)):
    if current_user.id != 1:
        raise HTTPException(403, "Admin only")
    ex = db.query(models.SharedExercise).filter(models.SharedExercise.id == exercise_id).first()
    if not ex:
        raise HTTPException(404, "Exercise not found")
    ex.status = "rejected"
    ex.approved_by = current_user.id
    db.commit(); db.refresh(ex)
    return _shared_out(ex, db)

@app.post("/api/shared-exercises/{exercise_id}/use", status_code=204)
def increment_use_count(exercise_id: int,
                         current_user: models.User = Depends(auth.get_current_user),
                         db: Session = Depends(get_db)):
    ex = db.query(models.SharedExercise).filter(
        models.SharedExercise.id == exercise_id,
        models.SharedExercise.status == "approved"
    ).first()
    if not ex:
        raise HTTPException(404, "Exercise not found")
    ex.use_count = (ex.use_count or 0) + 1
    db.commit()


# ── Serve PWA — MUST BE LAST (after all /api routes) ─────────────────────────

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static_assets")

    @app.get("/manifest.json")
    def manifest():
        return FileResponse(os.path.join(STATIC_DIR, "manifest.json"))

    @app.get("/sw.js")
    def service_worker():
        return FileResponse(os.path.join(STATIC_DIR, "sw.js"),
                            media_type="application/javascript",
                            headers={"Cache-Control": "no-store, no-cache, must-revalidate"})

    @app.get("/icons/{filename}")
    def icons(filename: str):
        return FileResponse(os.path.join(STATIC_DIR, "icons", filename))

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
