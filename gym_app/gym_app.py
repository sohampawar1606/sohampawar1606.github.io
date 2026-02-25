"""
IRONCORE GymApp — Flask Backend
Member App  : http://localhost:5000
Admin Panel : http://localhost:5000/admin

DATA STRUCTURES USED:
1. Hash Map (dict)         — O(1) user lookup, exercise index by category/level
2. Sorting (sorted())      — leaderboard, exercise results, equipment lists
3. Stack (list as stack)   — workout history (newest on top via insert(0,...))
4. Queue (deque)           — gym occupancy event log (fixed size, FIFO)
5. Set                     — tracking unique active categories
6. defaultdict             — goal/level distribution counting
7. Linked structure (list) — ordered exercise plan
"""

import hashlib
import json
import os
from datetime import date
from collections import defaultdict, deque
from flask import Flask, request, jsonify, render_template, session

app = Flask(__name__)
app.secret_key = "ironcore_secret_key_2024"

# ─────────────────────────────────────────────
#  DATA STRUCTURE 1: HASH MAP — Exercise Database
#  category -> level -> [exercises]  O(1) lookup
# ─────────────────────────────────────────────

EXERCISE_DB = {
    "chest": [
        {"name": "Bench Press",            "level": "intermediate", "calories": 250, "sets": 4, "reps": 8},
        {"name": "Push-Up",                "level": "beginner",     "calories": 150, "sets": 3, "reps": 15},
        {"name": "Incline Dumbbell Press", "level": "intermediate", "calories": 220, "sets": 4, "reps": 10},
        {"name": "Cable Fly",              "level": "advanced",     "calories": 200, "sets": 3, "reps": 12},
        {"name": "Chest Dip",              "level": "intermediate", "calories": 210, "sets": 3, "reps": 10},
        {"name": "Pec Deck Machine",       "level": "beginner",     "calories": 160, "sets": 3, "reps": 12},
        {"name": "Decline Bench Press",    "level": "advanced",     "calories": 260, "sets": 4, "reps": 8},
    ],
    "back": [
        {"name": "Pull-Up",             "level": "intermediate", "calories": 200, "sets": 4, "reps": 8},
        {"name": "Bent-Over Row",       "level": "intermediate", "calories": 230, "sets": 4, "reps": 10},
        {"name": "Lat Pulldown",        "level": "beginner",     "calories": 180, "sets": 3, "reps": 12},
        {"name": "Deadlift",            "level": "advanced",     "calories": 400, "sets": 3, "reps": 5},
        {"name": "Seated Cable Row",    "level": "beginner",     "calories": 170, "sets": 3, "reps": 12},
        {"name": "T-Bar Row",           "level": "intermediate", "calories": 240, "sets": 4, "reps": 8},
        {"name": "Single Arm Dumbbell Row","level":"intermediate","calories": 210, "sets": 3, "reps": 10},
        {"name": "Hyperextension",      "level": "beginner",     "calories": 130, "sets": 3, "reps": 15},
    ],
    "legs": [
        {"name": "Squat",                 "level": "intermediate", "calories": 350, "sets": 4, "reps": 8},
        {"name": "Leg Press",             "level": "beginner",     "calories": 280, "sets": 3, "reps": 12},
        {"name": "Romanian Deadlift",     "level": "intermediate", "calories": 300, "sets": 3, "reps": 10},
        {"name": "Bulgarian Split Squat", "level": "advanced",     "calories": 320, "sets": 3, "reps": 10},
        {"name": "Leg Curl",              "level": "beginner",     "calories": 160, "sets": 3, "reps": 12},
        {"name": "Leg Extension",         "level": "beginner",     "calories": 150, "sets": 3, "reps": 12},
        {"name": "Walking Lunges",        "level": "intermediate", "calories": 260, "sets": 3, "reps": 12},
        {"name": "Calf Raises",           "level": "beginner",     "calories": 120, "sets": 4, "reps": 20},
        {"name": "Box Jump",              "level": "advanced",     "calories": 340, "sets": 4, "reps": 8},
        {"name": "Sumo Squat",            "level": "intermediate", "calories": 280, "sets": 3, "reps": 12},
    ],
    "shoulders": [
        {"name": "Overhead Press",     "level": "intermediate", "calories": 220, "sets": 4, "reps": 8},
        {"name": "Lateral Raise",      "level": "beginner",     "calories": 130, "sets": 3, "reps": 15},
        {"name": "Arnold Press",       "level": "advanced",     "calories": 200, "sets": 4, "reps": 10},
        {"name": "Face Pull",          "level": "beginner",     "calories": 120, "sets": 3, "reps": 15},
        {"name": "Front Raise",        "level": "beginner",     "calories": 125, "sets": 3, "reps": 12},
        {"name": "Upright Row",        "level": "intermediate", "calories": 190, "sets": 3, "reps": 10},
        {"name": "Reverse Pec Deck",   "level": "intermediate", "calories": 150, "sets": 3, "reps": 12},
        {"name": "Shrugs",             "level": "beginner",     "calories": 140, "sets": 3, "reps": 15},
    ],
    "arms": [
        {"name": "Bicep Curl",          "level": "beginner",     "calories": 140, "sets": 3, "reps": 12},
        {"name": "Tricep Dip",          "level": "intermediate", "calories": 160, "sets": 3, "reps": 10},
        {"name": "Hammer Curl",         "level": "beginner",     "calories": 130, "sets": 3, "reps": 12},
        {"name": "Skull Crusher",       "level": "intermediate", "calories": 150, "sets": 3, "reps": 12},
        {"name": "Concentration Curl",  "level": "beginner",     "calories": 120, "sets": 3, "reps": 12},
        {"name": "Cable Tricep Pushdown","level": "beginner",    "calories": 130, "sets": 3, "reps": 15},
        {"name": "Preacher Curl",       "level": "intermediate", "calories": 145, "sets": 3, "reps": 10},
        {"name": "Overhead Tricep Ext", "level": "intermediate", "calories": 140, "sets": 3, "reps": 12},
        {"name": "Chin-Up",             "level": "advanced",     "calories": 180, "sets": 3, "reps": 8},
    ],
    "core": [
        {"name": "Plank",              "level": "beginner",     "calories": 100, "sets": 3, "reps": 60},
        {"name": "Hanging Leg Raise",  "level": "advanced",     "calories": 150, "sets": 3, "reps": 12},
        {"name": "Cable Crunch",       "level": "intermediate", "calories": 120, "sets": 3, "reps": 15},
        {"name": "Ab Wheel Rollout",   "level": "advanced",     "calories": 140, "sets": 3, "reps": 10},
        {"name": "Russian Twist",      "level": "beginner",     "calories": 110, "sets": 3, "reps": 20},
        {"name": "Mountain Climbers",  "level": "intermediate", "calories": 180, "sets": 3, "reps": 30},
        {"name": "Bicycle Crunch",     "level": "beginner",     "calories": 115, "sets": 3, "reps": 20},
        {"name": "Dragon Flag",        "level": "advanced",     "calories": 160, "sets": 3, "reps": 8},
        {"name": "Side Plank",         "level": "beginner",     "calories": 90,  "sets": 3, "reps": 45},
        {"name": "Decline Sit-Up",     "level": "intermediate", "calories": 130, "sets": 3, "reps": 15},
    ],
    "cardio": [
        {"name": "Treadmill Run",   "level": "beginner",     "calories": 400, "sets": 1, "reps": 30},
        {"name": "Cycling",         "level": "beginner",     "calories": 350, "sets": 1, "reps": 30},
        {"name": "Jump Rope",       "level": "intermediate", "calories": 450, "sets": 5, "reps": 2},
        {"name": "HIIT Sprints",    "level": "advanced",     "calories": 500, "sets": 8, "reps": 1},
        {"name": "Rowing Machine",  "level": "intermediate", "calories": 420, "sets": 1, "reps": 20},
        {"name": "Stair Climber",   "level": "intermediate", "calories": 380, "sets": 1, "reps": 20},
        {"name": "Battle Ropes",    "level": "advanced",     "calories": 480, "sets": 6, "reps": 1},
        {"name": "Burpees",         "level": "intermediate", "calories": 460, "sets": 5, "reps": 10},
        {"name": "Box Step-Up",     "level": "beginner",     "calories": 300, "sets": 3, "reps": 15},
        {"name": "Shadow Boxing",   "level": "beginner",     "calories": 320, "sets": 3, "reps": 3},
    ],
    "full_body": [
        {"name": "Clean and Press",   "level": "advanced",     "calories": 420, "sets": 4, "reps": 5},
        {"name": "Kettlebell Swing",  "level": "intermediate", "calories": 350, "sets": 4, "reps": 15},
        {"name": "Thruster",          "level": "advanced",     "calories": 400, "sets": 4, "reps": 8},
        {"name": "Man Maker",         "level": "advanced",     "calories": 380, "sets": 3, "reps": 8},
        {"name": "Turkish Get-Up",    "level": "intermediate", "calories": 300, "sets": 3, "reps": 5},
        {"name": "Dumbbell Complex",  "level": "intermediate", "calories": 340, "sets": 3, "reps": 8},
    ],
}

GOAL_MUSCLE_MAP = {
    "weight_loss":     ["cardio", "legs", "core"],
    "muscle_gain":     ["chest", "back", "legs", "shoulders", "arms"],
    "endurance":       ["cardio", "core", "legs", "full_body"],
    "flexibility":     ["core", "legs", "shoulders"],
    "general_fitness": ["chest", "back", "legs", "core", "cardio"],
    "strength":        ["legs", "back", "chest", "full_body"],
    "athletic":        ["full_body", "cardio", "legs", "core"],
}

LEVEL_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2}

# ─────────────────────────────────────────────
#  DATA STRUCTURE 1: HASH MAP — Exercise Index
# ─────────────────────────────────────────────
EXERCISE_INDEX = defaultdict(lambda: defaultdict(list))

def build_exercise_index():
    # DATA STRUCTURE 5: SET — track unique categories
    active_categories = set()
    for category, exercises in EXERCISE_DB.items():
        active_categories.add(category)
        for ex in exercises:
            EXERCISE_INDEX[category][ex["level"]].append({**ex, "category": category})
    return active_categories

ACTIVE_CATEGORIES = build_exercise_index()

def get_exercises(category, level):
    """O(1) hash map lookup"""
    return EXERCISE_INDEX.get(category, {}).get(level, [])

# ─────────────────────────────────────────────
#  DATA STRUCTURE 4: QUEUE — Gym Occupancy Log
#  Fixed-size deque tracks last 50 check-ins
# ─────────────────────────────────────────────
GYM_OCCUPANCY_LOG = deque(maxlen=50)
current_gym_count = 0  # live count of people in gym

# ─────────────────────────────────────────────
#  DEFAULT EQUIPMENT LIST
# ─────────────────────────────────────────────
DEFAULT_EQUIPMENT = [
    {"id":1, "name":"Treadmill",       "category":"Cardio",       "quantity":5, "condition":"Good",      "status":"Operational",  "last_service":"2026-01-15", "next_service":"2026-04-15"},
    {"id":2, "name":"Barbell Set",     "category":"Free Weights", "quantity":10,"condition":"Excellent", "status":"Operational",  "last_service":"2025-12-01", "next_service":"2026-06-01"},
    {"id":3, "name":"Smith Machine",   "category":"Strength",     "quantity":2, "condition":"Fair",      "status":"Service Due",  "last_service":"2025-11-20", "next_service":"2026-02-20"},
    {"id":4, "name":"Lat Pulldown",    "category":"Cable Machine","quantity":3, "condition":"Good",      "status":"Operational",  "last_service":"2026-01-05", "next_service":"2026-04-05"},
    {"id":5, "name":"Stationary Bike", "category":"Cardio",       "quantity":4, "condition":"Poor",      "status":"Needs Repair", "last_service":"2025-10-10", "next_service":"2026-01-10"},
    {"id":6, "name":"Dumbbell Rack",   "category":"Free Weights", "quantity":1, "condition":"Excellent", "status":"Operational",  "last_service":"2025-12-15", "next_service":"2026-06-15"},
    {"id":7, "name":"Pull-Up Station", "category":"Bodyweight",   "quantity":2, "condition":"Good",      "status":"Operational",  "last_service":"2026-01-20", "next_service":"2026-07-20"},
    {"id":8, "name":"Rowing Machine",  "category":"Cardio",       "quantity":3, "condition":"Good",      "status":"Operational",  "last_service":"2026-01-10", "next_service":"2026-04-10"},
    {"id":9, "name":"Cable Machine",   "category":"Cable Machine","quantity":2, "condition":"Good",      "status":"Operational",  "last_service":"2025-12-20", "next_service":"2026-03-20"},
    {"id":10,"name":"Leg Press",       "category":"Strength",     "quantity":2, "condition":"Good",      "status":"Operational",  "last_service":"2026-01-08", "next_service":"2026-04-08"},
]

# ─────────────────────────────────────────────
#  DATABASE HELPERS
# ─────────────────────────────────────────────
DB_FILE = "gym_database.json"

def hash_password(password):
    """DATA STRUCTURE 1: Hashing — SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def load_equipment():
    db = load_db()
    return db.get("__equipment__", DEFAULT_EQUIPMENT)

def save_equipment(equipment):
    db = load_db()
    db["__equipment__"] = equipment
    save_db(db)

def calc_bmi(weight, height):
    h = height / 100
    return round(weight / (h * h), 1)

def bmi_category(bmi):
    if bmi < 18.5: return "Underweight"
    elif bmi < 25:  return "Normal"
    elif bmi < 30:  return "Overweight"
    else:           return "Obese"

# ─────────────────────────────────────────────
#  RECOMMENDATION ENGINE
#  DATA STRUCTURE 2: Sorting — sort by calories
# ─────────────────────────────────────────────
def recommend(goal, level):
    categories = GOAL_MUSCLE_MAP.get(goal, ["cardio", "core"])
    exercises = []
    # DATA STRUCTURE 5: SET — avoid duplicate categories
    seen_categories = set()
    for cat in categories:
        if cat in seen_categories:
            continue
        seen_categories.add(cat)
        found = get_exercises(cat, level)
        if not found:
            found = get_exercises(cat, "beginner")
        if found:
            # DATA STRUCTURE 2: SORTING — pick highest calorie exercise
            best = sorted(found, key=lambda e: e["calories"], reverse=True)[0]
            exercises.append(best)
    # DATA STRUCTURE 2: SORTING — sort full plan by calories desc
    return sorted(exercises, key=lambda e: e["calories"], reverse=True)

# ─────────────────────────────────────────────
#  PAGES
# ─────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin")
def admin():
    return render_template("admin.html")

# ─────────────────────────────────────────────
#  MEMBER API — Auth
# ─────────────────────────────────────────────
@app.route("/api/register", methods=["POST"])
def register():
    data     = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")
    age      = int(data.get("age", 0))
    weight   = float(data.get("weight", 0))
    height   = float(data.get("height", 0))
    goal     = data.get("goal", "general_fitness")
    level    = data.get("level", "beginner")

    if not all([username, password, age, weight, height]):
        return jsonify({"success": False, "message": "All fields are required"}), 400

    db = load_db()
    # DATA STRUCTURE 1: HASH MAP — O(1) check if user exists
    if username in db or username == "__equipment__":
        return jsonify({"success": False, "message": "Username already exists"}), 409

    # DATA STRUCTURE 1: HASH MAP — store user by username key
    db[username] = {
        "username":      username,
        "password_hash": hash_password(password),  # HASHING
        "age":           age,
        "weight":        weight,
        "height":        height,
        "goal":          goal,
        "level":         level,
        "joined":        str(date.today()),
        "history":       []  # DATA STRUCTURE 3: STACK — newest workout on top
    }
    save_db(db)
    return jsonify({"success": True, "message": "Account created!"})


@app.route("/api/login", methods=["POST"])
def login():
    data     = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")
    db       = load_db()
    # DATA STRUCTURE 1: HASH MAP — O(1) user lookup
    user     = db.get(username)
    if not user or user.get("password_hash") != hash_password(password):
        return jsonify({"success": False, "message": "Invalid credentials"}), 401
    session["username"] = username
    bmi = calc_bmi(user["weight"], user["height"])
    return jsonify({
        "success": True,
        "user": {
            "username":       user["username"],
            "age":            user["age"],
            "weight":         user["weight"],
            "height":         user["height"],
            "goal":           user["goal"],
            "level":          user["level"],
            "bmi":            bmi,
            "bmi_category":   bmi_category(bmi),
            "workout_count":  len(user["history"]),
            "total_calories": sum(h["total_calories"] for h in user["history"]),
        }
    })


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})

# ─────────────────────────────────────────────
#  MEMBER API — Workout
# ─────────────────────────────────────────────
@app.route("/api/recommend", methods=["GET"])
def get_recommendation():
    if "username" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401
    db    = load_db()
    user  = db[session["username"]]
    goal  = request.args.get("goal",  user["goal"])
    level = request.args.get("level", user["level"])
    exercises = recommend(goal, level)
    return jsonify({
        "success":        True,
        "goal":           goal,
        "level":          level,
        "exercises":      exercises,
        "total_calories": sum(e["calories"] for e in exercises)
    })


@app.route("/api/save_workout", methods=["POST"])
def save_workout():
    if "username" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401
    data = request.json
    db   = load_db()
    # DATA STRUCTURE 3: STACK — insert at index 0 (push to top)
    db[session["username"]]["history"].insert(0, {
        "date":           str(date.today()),
        "goal":           data["goal"],
        "level":          data["level"],
        "total_calories": data["total_calories"],
        "exercises":      data["exercises"]
    })
    save_db(db)
    return jsonify({"success": True, "message": "Workout saved!"})

# ─────────────────────────────────────────────
#  MEMBER API — Exercises
# ─────────────────────────────────────────────
@app.route("/api/exercises", methods=["GET"])
def get_exercises_api():
    category = request.args.get("category", "all")
    keyword  = request.args.get("search", "").lower()
    all_exs  = []
    # DATA STRUCTURE 5: SET — get unique active categories
    cats = list(ACTIVE_CATEGORIES) if category == "all" else [category]
    for cat in cats:
        for level_exs in EXERCISE_INDEX.get(cat, {}).values():
            all_exs.extend(level_exs)
    if keyword:
        all_exs = [e for e in all_exs if keyword in e["name"].lower()
                   or keyword in e["category"].lower() or keyword in e["level"].lower()]
    # DATA STRUCTURE 2: SORTING — by level then calories desc
    all_exs.sort(key=lambda e: (LEVEL_ORDER[e["level"]], -e["calories"]))
    return jsonify({"success": True, "exercises": all_exs,
                    "categories": sorted(list(ACTIVE_CATEGORIES))})

# ─────────────────────────────────────────────
#  MEMBER API — History
# ─────────────────────────────────────────────
@app.route("/api/history", methods=["GET"])
def get_history():
    if "username" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401
    db = load_db()
    return jsonify({"success": True, "history": db[session["username"]]["history"]})


@app.route("/api/history", methods=["DELETE"])
def clear_history():
    if "username" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401
    db = load_db()
    db[session["username"]]["history"] = []
    save_db(db)
    return jsonify({"success": True})

# ─────────────────────────────────────────────
#  MEMBER API — Profile
# ─────────────────────────────────────────────
@app.route("/api/profile", methods=["PUT"])
def update_profile():
    if "username" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401
    data = request.json
    db   = load_db()
    user = db[session["username"]]
    user["weight"] = float(data.get("weight", user["weight"]))
    user["height"] = float(data.get("height", user["height"]))
    user["goal"]   = data.get("goal",  user["goal"])
    user["level"]  = data.get("level", user["level"])
    save_db(db)
    bmi = calc_bmi(user["weight"], user["height"])
    return jsonify({"success": True, "bmi": bmi, "bmi_category": bmi_category(bmi)})

# ─────────────────────────────────────────────
#  MEMBER API — Leaderboard
# ─────────────────────────────────────────────
@app.route("/api/leaderboard", methods=["GET"])
def leaderboard():
    db = load_db()
    # DATA STRUCTURE 2: SORTING — sort by workout count desc
    board = sorted(
        [{"username": u["username"], "count": len(u["history"])}
         for k, u in db.items() if k != "__equipment__"],
        key=lambda x: x["count"], reverse=True
    )
    return jsonify({"success": True, "leaderboard": board})

# ─────────────────────────────────────────────
#  FEATURE 3: GYM OCCUPANCY — Members can see
#  how crowded the gym is in real time
# ─────────────────────────────────────────────
@app.route("/api/gym/occupancy", methods=["GET"])
def get_occupancy():
    max_capacity = 50
    pct = round((current_gym_count / max_capacity) * 100)
    if pct < 30:   status = "Not Crowded"
    elif pct < 60: status = "Moderate"
    elif pct < 85: status = "Busy"
    else:          status = "Very Crowded"
    return jsonify({
        "success":      True,
        "count":        current_gym_count,
        "max_capacity": max_capacity,
        "percentage":   pct,
        "status":       status,
        # DATA STRUCTURE 4: QUEUE — last 10 check-in events
        "recent_log":   list(GYM_OCCUPANCY_LOG)[-10:]
    })

# ─────────────────────────────────────────────
#  ADMIN API — Login/Logout
# ─────────────────────────────────────────────
ADMIN_PASSWORD = "admin123"

@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    data = request.json
    if data.get("password") == ADMIN_PASSWORD:
        session["is_admin"] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Invalid admin password"}), 401


@app.route("/api/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("is_admin", None)
    return jsonify({"success": True})

# ─────────────────────────────────────────────
#  ADMIN API — Stats
# ─────────────────────────────────────────────
@app.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    if not session.get("is_admin"):
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    db = load_db()
    members = {k: v for k, v in db.items() if k != "__equipment__"}

    total_members  = len(members)
    total_workouts = sum(len(u["history"]) for u in members.values())
    total_calories = sum(sum(h["total_calories"] for h in u["history"]) for u in members.values())

    # DATA STRUCTURE 6: defaultdict — count goals and levels
    goal_count  = defaultdict(int)
    level_count = defaultdict(int)
    for u in members.values():
        goal_count[u["goal"]]   += 1
        level_count[u["level"]] += 1

    # DATA STRUCTURE 2: SORTING — find most active
    most_active = max(members.values(), key=lambda u: len(u["history"]), default=None)

    return jsonify({
        "success":            True,
        "total_members":      total_members,
        "total_workouts":     total_workouts,
        "total_calories":     total_calories,
        "goal_distribution":  dict(goal_count),
        "level_distribution": dict(level_count),
        "most_active":        most_active["username"] if most_active else "N/A",
        "gym_count":          current_gym_count,
    })

# ─────────────────────────────────────────────
#  ADMIN API — Members
# ─────────────────────────────────────────────
@app.route("/api/admin/members", methods=["GET"])
def admin_get_members():
    if not session.get("is_admin"):
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    db = load_db()
    members = []
    for k, u in db.items():
        if k == "__equipment__":
            continue
        bmi = calc_bmi(u["weight"], u["height"])
        members.append({
            "username":       u["username"],
            "age":            u["age"],
            "weight":         u["weight"],
            "height":         u["height"],
            "goal":           u["goal"],
            "level":          u["level"],
            "workout_count":  len(u["history"]),
            "total_calories": sum(h["total_calories"] for h in u["history"]),
            "joined":         u.get("joined", "N/A"),
            "bmi":            bmi,
            "bmi_category":   bmi_category(bmi),
        })
    # DATA STRUCTURE 2: SORTING
    members.sort(key=lambda x: x["workout_count"], reverse=True)
    return jsonify({"success": True, "members": members, "total": len(members)})


@app.route("/api/admin/members", methods=["POST"])
def admin_add_member():
    if not session.get("is_admin"):
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    data     = request.json
    username = data.get("username", "").strip()
    if not username:
        return jsonify({"success": False, "message": "Username required"}), 400
    db = load_db()
    if username in db:
        return jsonify({"success": False, "message": "Username already exists"}), 409
    db[username] = {
        "username":      username,
        "password_hash": hash_password(data.get("password", "changeme123")),
        "age":           int(data.get("age", 25)),
        "weight":        float(data.get("weight", 70)),
        "height":        float(data.get("height", 170)),
        "goal":          data.get("goal",  "general_fitness"),
        "level":         data.get("level", "beginner"),
        "joined":        str(date.today()),
        "history":       []
    }
    save_db(db)
    return jsonify({"success": True, "message": f"{username} added!"})


@app.route("/api/admin/members/<username>", methods=["DELETE"])
def admin_delete_member(username):
    if not session.get("is_admin"):
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    db = load_db()
    if username not in db:
        return jsonify({"success": False, "message": "Not found"}), 404
    del db[username]
    save_db(db)
    return jsonify({"success": True})


@app.route("/api/admin/members/<username>/history", methods=["GET"])
def admin_member_history(username):
    if not session.get("is_admin"):
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    db = load_db()
    if username not in db:
        return jsonify({"success": False, "message": "Not found"}), 404
    return jsonify({"success": True, "history": db[username]["history"]})

# ─────────────────────────────────────────────
#  FEATURE 1: ADMIN API — Equipment (LIVE, editable)
#  All changes saved to gym_database.json
# ─────────────────────────────────────────────
@app.route("/api/admin/equipment", methods=["GET"])
def get_equipment():
    if not session.get("is_admin"):
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    equipment = load_equipment()
    # DATA STRUCTURE 2: SORTING — sort by name
    equipment = sorted(equipment, key=lambda e: e["name"])
    return jsonify({"success": True, "equipment": equipment})


@app.route("/api/admin/equipment", methods=["POST"])
def add_equipment():
    if not session.get("is_admin"):
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    data      = request.json
    equipment = load_equipment()
    # Generate new ID
    new_id = max((e["id"] for e in equipment), default=0) + 1
    new_item  = {
        "id":           new_id,
        "name":         data.get("name", ""),
        "category":     data.get("category", "Other"),
        "quantity":     int(data.get("quantity", 1)),
        "condition":    data.get("condition", "Good"),
        "status":       data.get("status", "Operational"),
        "last_service": data.get("last_service", str(date.today())),
        "next_service": data.get("next_service", ""),
    }
    if not new_item["name"]:
        return jsonify({"success": False, "message": "Equipment name required"}), 400
    equipment.append(new_item)
    save_equipment(equipment)
    return jsonify({"success": True, "message": f"{new_item['name']} added!", "equipment": new_item})


@app.route("/api/admin/equipment/<int:eq_id>", methods=["PUT"])
def update_equipment(eq_id):
    if not session.get("is_admin"):
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    data      = request.json
    equipment = load_equipment()
    # DATA STRUCTURE 1: HASH MAP style lookup by id
    for item in equipment:
        if item["id"] == eq_id:
            item["name"]         = data.get("name",         item["name"])
            item["category"]     = data.get("category",     item["category"])
            item["quantity"]     = int(data.get("quantity", item["quantity"]))
            item["condition"]    = data.get("condition",    item["condition"])
            item["status"]       = data.get("status",       item["status"])
            item["last_service"] = data.get("last_service", item["last_service"])
            item["next_service"] = data.get("next_service", item["next_service"])
            save_equipment(equipment)
            return jsonify({"success": True, "message": "Equipment updated!", "equipment": item})
    return jsonify({"success": False, "message": "Equipment not found"}), 404


@app.route("/api/admin/equipment/<int:eq_id>", methods=["DELETE"])
def delete_equipment(eq_id):
    if not session.get("is_admin"):
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    equipment = load_equipment()
    equipment = [e for e in equipment if e["id"] != eq_id]
    save_equipment(equipment)
    return jsonify({"success": True, "message": "Equipment removed"})

# ─────────────────────────────────────────────
#  FEATURE 3: ADMIN — Set Gym Occupancy
# ─────────────────────────────────────────────
@app.route("/api/admin/occupancy", methods=["PUT"])
def set_occupancy():
    if not session.get("is_admin"):
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    global current_gym_count
    data  = request.json
    count = int(data.get("count", 0))
    current_gym_count = max(0, min(count, 50))
    # DATA STRUCTURE 4: QUEUE — log the event (auto drops oldest if > 50)
    GYM_OCCUPANCY_LOG.append({
        "count": current_gym_count,
        "time":  str(date.today()),
        "action": data.get("action", "manual update")
    })
    return jsonify({"success": True, "count": current_gym_count})

# ─────────────────────────────────────────────
#  RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🏋️  IRONCORE GymApp is running!")
    print("   Member App : http://localhost:5000")
    print("   Admin Panel: http://localhost:5000/admin")
    print("\n📦 Data Structures Used:")
    print("   1. Hash Map   — User/exercise O(1) lookup + password hashing")
    print("   2. Sorting    — Leaderboard, exercises, equipment, workout plans")
    print("   3. Stack      — Workout history (newest on top)")
    print("   4. Queue      — Gym occupancy event log (deque, maxlen=50)")
    print("   5. Set        — Unique categories, duplicate prevention")
    print("   6. defaultdict — Goal/level distribution counting\n")
    app.run(debug=True, port=5000)
