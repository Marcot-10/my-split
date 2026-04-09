import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

raw_url = os.getenv("DATABASE_URL", "sqlite:///./mysplit.db")
DATABASE_URL = raw_url.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

SEED_EXERCISES = [
    {"id":"e_bench_press","name":"Bench Press","primary_muscle":"chest","secondary_muscles":["triceps","shoulders"],"category":"compound","equipment":"barbell"},
    {"id":"e_incline_bench","name":"Incline Barbell Press","primary_muscle":"chest","secondary_muscles":["triceps","shoulders"],"category":"compound","equipment":"barbell"},
    {"id":"e_decline_bench","name":"Decline Barbell Press","primary_muscle":"chest","secondary_muscles":["triceps"],"category":"compound","equipment":"barbell"},
    {"id":"e_incline_db_press","name":"Incline Dumbbell Press","primary_muscle":"chest","secondary_muscles":["triceps","shoulders"],"category":"compound","equipment":"dumbbell"},
    {"id":"e_flat_db_press","name":"Flat Dumbbell Press","primary_muscle":"chest","secondary_muscles":["triceps"],"category":"compound","equipment":"dumbbell"},
    {"id":"e_chest_press_machine","name":"Chest Press Machine","primary_muscle":"chest","secondary_muscles":["triceps","shoulders"],"category":"compound","equipment":"machine"},
    {"id":"e_incline_plate_press","name":"Incline Plate Press","primary_muscle":"chest","secondary_muscles":["triceps","shoulders"],"category":"compound","equipment":"plate"},
    {"id":"e_cable_fly","name":"Cable Fly","primary_muscle":"chest","secondary_muscles":[],"category":"isolation","equipment":"cable"},
    {"id":"e_machine_fly","name":"Machine Fly / Pec Deck","primary_muscle":"chest","secondary_muscles":[],"category":"isolation","equipment":"machine"},
    {"id":"e_standing_fly","name":"Standing Cable Fly","primary_muscle":"chest","secondary_muscles":["shoulders"],"category":"isolation","equipment":"cable"},
    {"id":"e_dip","name":"Chest Dip","primary_muscle":"chest","secondary_muscles":["triceps","shoulders"],"category":"compound","equipment":"bodyweight"},
    {"id":"e_pushup","name":"Push-Up","primary_muscle":"chest","secondary_muscles":["triceps","shoulders"],"category":"compound","equipment":"bodyweight"},
    {"id":"e_lat_pulldown","name":"Lat Pulldown","primary_muscle":"back","secondary_muscles":["biceps"],"category":"compound","equipment":"cable"},
    {"id":"e_pullup","name":"Pull-Up","primary_muscle":"back","secondary_muscles":["biceps"],"category":"compound","equipment":"bodyweight"},
    {"id":"e_chinup","name":"Chin-Up","primary_muscle":"back","secondary_muscles":["biceps"],"category":"compound","equipment":"bodyweight"},
    {"id":"e_seated_row","name":"Seated Cable Row","primary_muscle":"back","secondary_muscles":["biceps"],"category":"compound","equipment":"cable"},
    {"id":"e_cs_row","name":"Chest Supported Row","primary_muscle":"back","secondary_muscles":["biceps","rear delts"],"category":"compound","equipment":"machine"},
    {"id":"e_single_arm_row","name":"Single Arm Dumbbell Row","primary_muscle":"back","secondary_muscles":["biceps"],"category":"compound","equipment":"dumbbell"},
    {"id":"e_sa_plate_row","name":"Single Arm Plate Row","primary_muscle":"back","secondary_muscles":["biceps"],"category":"compound","equipment":"plate"},
    {"id":"e_bb_row","name":"Barbell Bent-Over Row","primary_muscle":"back","secondary_muscles":["biceps","hamstrings"],"category":"compound","equipment":"barbell"},
    {"id":"e_face_pull","name":"Face Pull","primary_muscle":"back","secondary_muscles":["rear delts","shoulders"],"category":"isolation","equipment":"cable"},
    {"id":"e_deadlift","name":"Deadlift","primary_muscle":"back","secondary_muscles":["hamstrings","glutes"],"category":"compound","equipment":"barbell"},
    {"id":"e_rack_pull","name":"Rack Pull","primary_muscle":"back","secondary_muscles":["hamstrings","glutes"],"category":"compound","equipment":"barbell"},
    # Traps
    {"id":"e_barbell_shrug","name":"Barbell Shrug","primary_muscle":"traps","secondary_muscles":[],"category":"isolation","equipment":"barbell"},
    {"id":"e_db_shrug","name":"Dumbbell Shrug","primary_muscle":"traps","secondary_muscles":[],"category":"isolation","equipment":"dumbbell"},
    {"id":"e_cable_shrug","name":"Cable Shrug","primary_muscle":"traps","secondary_muscles":[],"category":"isolation","equipment":"cable"},
    {"id":"e_trap_bar_deadlift","name":"Trap Bar Deadlift","primary_muscle":"traps","secondary_muscles":["back","hamstrings","glutes"],"category":"compound","equipment":"barbell"},
    {"id":"e_db_upright_row","name":"Dumbbell Upright Row","primary_muscle":"traps","secondary_muscles":["shoulders"],"category":"compound","equipment":"dumbbell"},
    {"id":"e_ohp","name":"Overhead Barbell Press","primary_muscle":"shoulders","secondary_muscles":["triceps"],"category":"compound","equipment":"barbell"},
    {"id":"e_db_shoulder_press","name":"Dumbbell Shoulder Press","primary_muscle":"shoulders","secondary_muscles":["triceps"],"category":"compound","equipment":"dumbbell"},
    {"id":"e_machine_shoulder_press","name":"Machine Shoulder Press","primary_muscle":"shoulders","secondary_muscles":["triceps"],"category":"compound","equipment":"machine"},
    {"id":"e_lateral_raise","name":"Dumbbell Lateral Raise","primary_muscle":"shoulders","secondary_muscles":[],"category":"isolation","equipment":"dumbbell"},
    {"id":"e_lateral_raise_machine","name":"Lateral Raise Machine","primary_muscle":"shoulders","secondary_muscles":[],"category":"isolation","equipment":"machine"},
    {"id":"e_cable_lateral","name":"Cable Lateral Raise","primary_muscle":"shoulders","secondary_muscles":[],"category":"isolation","equipment":"cable"},
    {"id":"e_rear_delt_machine","name":"Rear Delt Machine","primary_muscle":"shoulders","secondary_muscles":["back"],"category":"isolation","equipment":"machine"},
    {"id":"e_reverse_fly","name":"Reverse Fly / Pec Deck","primary_muscle":"shoulders","secondary_muscles":["back"],"category":"isolation","equipment":"machine"},
    {"id":"e_arnold_press","name":"Arnold Press","primary_muscle":"shoulders","secondary_muscles":["triceps"],"category":"compound","equipment":"dumbbell"},
    {"id":"e_barbell_curl","name":"Barbell Curl","primary_muscle":"biceps","secondary_muscles":["forearms"],"category":"isolation","equipment":"barbell"},
    {"id":"e_db_curl","name":"Dumbbell Curl","primary_muscle":"biceps","secondary_muscles":["forearms"],"category":"isolation","equipment":"dumbbell"},
    {"id":"e_hammer_curl","name":"Hammer Curl","primary_muscle":"biceps","secondary_muscles":["forearms"],"category":"isolation","equipment":"dumbbell"},
    {"id":"e_preacher_curl","name":"Preacher Curl","primary_muscle":"biceps","secondary_muscles":[],"category":"isolation","equipment":"machine"},
    {"id":"e_bayesian_curl","name":"Bayesian Cable Curl","primary_muscle":"biceps","secondary_muscles":[],"category":"isolation","equipment":"cable"},
    {"id":"e_incline_curl","name":"Incline Dumbbell Curl","primary_muscle":"biceps","secondary_muscles":[],"category":"isolation","equipment":"dumbbell"},
    {"id":"e_concentration_curl","name":"Concentration Curl","primary_muscle":"biceps","secondary_muscles":[],"category":"isolation","equipment":"dumbbell"},
    {"id":"e_cable_curl","name":"Cable Curl","primary_muscle":"biceps","secondary_muscles":["forearms"],"category":"isolation","equipment":"cable"},  # deduplicated
    {"id":"e_spider_curl","name":"Spider Curl","primary_muscle":"biceps","secondary_muscles":[],"category":"isolation","equipment":"dumbbell"},
    {"id":"e_pushdown","name":"Tricep Pushdown","primary_muscle":"triceps","secondary_muscles":[],"category":"isolation","equipment":"cable"},
    {"id":"e_overhead_ext","name":"Overhead Tricep Extension","primary_muscle":"triceps","secondary_muscles":[],"category":"isolation","equipment":"cable"},
    {"id":"e_kickback","name":"Tricep Kickback","primary_muscle":"triceps","secondary_muscles":[],"category":"isolation","equipment":"dumbbell"},
    {"id":"e_skullcrusher","name":"Skull Crusher","primary_muscle":"triceps","secondary_muscles":[],"category":"isolation","equipment":"barbell"},
    {"id":"e_close_grip_bench","name":"Close-Grip Bench Press","primary_muscle":"triceps","secondary_muscles":["chest"],"category":"compound","equipment":"barbell"},
    {"id":"e_rope_pushdown","name":"Rope Pushdown","primary_muscle":"triceps","secondary_muscles":[],"category":"isolation","equipment":"cable"},
    {"id":"e_db_overhead_ext","name":"Dumbbell Overhead Extension","primary_muscle":"triceps","secondary_muscles":[],"category":"isolation","equipment":"dumbbell"},
    {"id":"e_tricep_dip","name":"Tricep Dip","primary_muscle":"triceps","secondary_muscles":["chest","shoulders"],"category":"compound","equipment":"bodyweight"},
    {"id":"e_squat","name":"Barbell Back Squat","primary_muscle":"quads","secondary_muscles":["glutes","hamstrings"],"category":"compound","equipment":"barbell"},
    {"id":"e_front_squat","name":"Front Squat","primary_muscle":"quads","secondary_muscles":["glutes"],"category":"compound","equipment":"barbell"},
    {"id":"e_hack_squat","name":"Hack Squat","primary_muscle":"quads","secondary_muscles":["glutes"],"category":"compound","equipment":"machine"},
    {"id":"e_leg_press","name":"Leg Press","primary_muscle":"quads","secondary_muscles":["glutes","hamstrings"],"category":"compound","equipment":"machine"},
    {"id":"e_sa_leg_press","name":"Single Seated Machine Leg Press","primary_muscle":"quads","secondary_muscles":["glutes"],"category":"compound","equipment":"machine"},
    {"id":"e_leg_ext","name":"Leg Extension","primary_muscle":"quads","secondary_muscles":[],"category":"isolation","equipment":"machine"},
    {"id":"e_bulgarian","name":"Bulgarian Split Squat","primary_muscle":"quads","secondary_muscles":["glutes","hamstrings"],"category":"compound","equipment":"dumbbell"},
    {"id":"e_lunge","name":"Dumbbell Lunge","primary_muscle":"quads","secondary_muscles":["glutes","hamstrings"],"category":"compound","equipment":"dumbbell"},
    {"id":"e_rdl","name":"Romanian Deadlift","primary_muscle":"hamstrings","secondary_muscles":["glutes","back"],"category":"compound","equipment":"barbell"},
    {"id":"e_db_rdl","name":"Dumbbell Romanian Deadlift","primary_muscle":"hamstrings","secondary_muscles":["glutes"],"category":"compound","equipment":"dumbbell"},
    {"id":"e_leg_curl","name":"Lying Leg Curl","primary_muscle":"hamstrings","secondary_muscles":[],"category":"isolation","equipment":"machine"},
    {"id":"e_seated_leg_curl","name":"Seated Leg Curl","primary_muscle":"hamstrings","secondary_muscles":[],"category":"isolation","equipment":"machine"},
    {"id":"e_nordic_curl","name":"Nordic Curl","primary_muscle":"hamstrings","secondary_muscles":[],"category":"isolation","equipment":"bodyweight"},
    {"id":"e_hip_thrust","name":"Barbell Hip Thrust","primary_muscle":"glutes","secondary_muscles":["hamstrings"],"category":"compound","equipment":"barbell"},
    {"id":"e_glute_bridge","name":"Glute Bridge","primary_muscle":"glutes","secondary_muscles":[],"category":"compound","equipment":"bodyweight"},
    {"id":"e_adduction","name":"Adduction Machine","primary_muscle":"glutes","secondary_muscles":["quads"],"category":"isolation","equipment":"machine"},
    {"id":"e_abduction","name":"Abduction Machine","primary_muscle":"glutes","secondary_muscles":[],"category":"isolation","equipment":"machine"},
    {"id":"e_standing_calf","name":"Standing Calf Raise","primary_muscle":"calves","secondary_muscles":[],"category":"isolation","equipment":"machine"},
    {"id":"e_seated_calf","name":"Seated Calf Raise","primary_muscle":"calves","secondary_muscles":[],"category":"isolation","equipment":"machine"},
    {"id":"e_leg_press_calf","name":"Leg Press Calf Raise","primary_muscle":"calves","secondary_muscles":[],"category":"isolation","equipment":"machine"},
    {"id":"e_ab_machine","name":"Ab Machine / Crunch Machine","primary_muscle":"abs","secondary_muscles":[],"category":"isolation","equipment":"machine"},
    {"id":"e_hanging_leg_raise","name":"Hanging Leg Raise","primary_muscle":"abs","secondary_muscles":["hip flexors"],"category":"isolation","equipment":"bodyweight"},
    {"id":"e_cable_crunch","name":"Cable Crunch","primary_muscle":"abs","secondary_muscles":[],"category":"isolation","equipment":"cable"},
    {"id":"e_plank","name":"Plank","primary_muscle":"abs","secondary_muscles":["shoulders"],"category":"isolation","equipment":"bodyweight"},
    {"id":"e_ab_wheel","name":"Ab Wheel Rollout","primary_muscle":"abs","secondary_muscles":["back","shoulders"],"category":"isolation","equipment":"bodyweight"},
    {"id":"e_leg_raise","name":"Lying Leg Raise","primary_muscle":"abs","secondary_muscles":[],"category":"isolation","equipment":"bodyweight"},
    # Push
    {"id":"e_pec_deck","name":"Pec Deck Machine","primary_muscle":"chest","secondary_muscles":[],"category":"isolation","equipment":"machine"},
    # Pull
    {"id":"e_straight_arm_pulldown","name":"Straight-Arm Pulldown","primary_muscle":"back","secondary_muscles":[],"category":"isolation","equipment":"cable"},
    {"id":"e_reverse_curl","name":"Reverse Curl","primary_muscle":"forearms","secondary_muscles":["biceps"],"category":"isolation","equipment":"barbell"},
    # Legs
    {"id":"e_walking_lunge","name":"Walking Lunges","primary_muscle":"quads","secondary_muscles":["glutes","hamstrings"],"category":"compound","equipment":"dumbbell"},
    {"id":"e_tibialis_raise","name":"Tibialis Raise","primary_muscle":"calves","secondary_muscles":[],"category":"isolation","equipment":"bodyweight"},
    {"id":"e_adduction_machine","name":"Adduction Machine","primary_muscle":"glutes","secondary_muscles":["quads"],"category":"isolation","equipment":"machine"},
    # Core / Full Body
    {"id":"e_pallof_press","name":"Pallof Press","primary_muscle":"abs","secondary_muscles":["back"],"category":"isolation","equipment":"cable"},
    {"id":"e_farmers_carry","name":"Farmers Carry","primary_muscle":"back","secondary_muscles":["traps","core"],"category":"compound","equipment":"dumbbell"},
    {"id":"e_suitcase_carry","name":"Suitcase Carry","primary_muscle":"abs","secondary_muscles":["back","traps"],"category":"compound","equipment":"dumbbell"},
    # Posterior chain
    {"id":"e_back_extension","name":"Back Extension","primary_muscle":"back","secondary_muscles":["glutes","hamstrings"],"category":"isolation","equipment":"bodyweight"},
    # Cardio
    {"id":"e_stairmaster","name":"Stairmaster","primary_muscle":"quads","secondary_muscles":["glutes","calves"],"category":"compound","equipment":"machine"},
    {"id":"e_rowing_machine","name":"Rowing Machine","primary_muscle":"back","secondary_muscles":["biceps","shoulders"],"category":"compound","equipment":"machine"},
    {"id":"e_sled_push","name":"Sled Push","primary_muscle":"quads","secondary_muscles":["glutes","shoulders"],"category":"compound","equipment":"machine"},
    {"id":"e_battle_ropes","name":"Battle Ropes","primary_muscle":"shoulders","secondary_muscles":["back","abs"],"category":"compound","equipment":"bodyweight"},
]

def seed_exercises(db):
    from models import Exercise
    for data in SEED_EXERCISES:
        if not db.query(Exercise).filter(Exercise.id == data["id"]).first():
            db.add(Exercise(**data, user_id=None, is_custom=False))
    db.commit()
