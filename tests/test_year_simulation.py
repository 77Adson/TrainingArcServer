import requests
import datetime
import uuid
import random

# --- CONFIGURATION ---
BASE_URL = "http://192.168.0.108:5000"  # Change to your server IP if not local
EMAIL = "userAuto@test.com"
PASSWORD = "123"
DAYS_TO_SIMULATE = 365

session = requests.Session()
headers = {}

def print_step(msg):
    print(f"[*] {msg}")

def run_simulation():
    print("==================================================")
    print("🏋️  TRAINING ARC: 1-YEAR USER SIMULATION STARTING  🏋️")
    print("==================================================")

    # 1. REGISTER OR LOGIN
    payload = {"email": EMAIL, "password": PASSWORD}
    r = session.post(f"{BASE_URL}/register", json=payload)
    if r.status_code in [201, 409]: # 409 means already exists
        r = session.post(f"{BASE_URL}/login", json=payload)
        token = r.json().get("access_token")
        headers["Authorization"] = f"Bearer {token}"
        print_step(f"Logged in successfully as {EMAIL}")
    else:
        print(f"Failed to auth: {r.text}")
        return

    # 2. UPDATE PROFILE
    session.patch(f"{BASE_URL}/user", headers=headers, json={
        "username": "AutoGrinder",
        "weight": 80.0
    })
    print_step("Profile updated.")

    # 3. CREATE EXERCISES
    exercises = [
        {"name": "Bench Press", "type": "compound", "base_w": 40.0, "goal": "3x8"},
        {"name": "Pull-ups", "type": "bodyweight", "base_w": 0.0, "goal": "3xFailure"},
        {"name": "Bicep Curls", "type": "isolation", "base_w": 10.0, "goal": "3x12"},
        {"name": "5K Run", "type": "running", "base_w": 0.0, "goal": "Sub 25m"}
    ]
    
    ex_ids = {}
    for ex in exercises:
        r = session.post(f"{BASE_URL}/user/exercises", headers=headers, json={"name": ex["name"]})
        ex_id = r.json()["exercise_id"]
        # Update type and goal
        session.patch(f"{BASE_URL}/user/exercises/{ex_id}", headers=headers, json={
            "main_type": ex["type"],
            "goal": ex["goal"]
        })
        ex_ids[ex["name"]] = ex_id
    
    print_step("4 Base Exercises created and configured.")

    # 4. CREATE WORKOUT PLAN
    r = session.post(f"{BASE_URL}/user/workouts", headers=headers, json={"name": "The Year Long Grind"})
    workout_id = r.json()["workout_id"]
    
    session.patch(f"{BASE_URL}/user/workouts/{workout_id}", headers=headers, json={
        "days_of_week": {"Monday": True, "Wednesday": True, "Friday": True, "Tuesday": False, "Thursday": False, "Saturday": False, "Sunday": False},
        "exercise_groups": [
            {"name": "Heavy Lifts", "exercise_ids": [ex_ids["Bench Press"], ex_ids["Pull-ups"]]},
            {"name": "Accessories & Cardio", "exercise_ids": [ex_ids["Bicep Curls"], ex_ids["5K Run"]]}
        ]
    })
    print_step(f"Workout Blueprint created (ID: {workout_id}).")

    # 5. SIMULATE 1 YEAR OF WORKOUTS (Mon, Wed, Fri)
    print_step("Beginning time-travel simulation... This may take a minute.")
    
    start_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=DAYS_TO_SIMULATE)
    
    workouts_completed = 0
    
    for day_offset in range(DAYS_TO_SIMULATE + 1):
        current_date = start_date + datetime.timedelta(days=day_offset)
        
        # Only workout on Mon (0), Wed (2), Fri (4)
        if current_date.weekday() not in [0, 2, 4]:
            continue

        session_id = str(uuid.uuid4())
        date_str = current_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Progression Math: Small linear increase over the year + some randomness
        progress_factor = day_offset / 365.0 # 0.0 to 1.0
        
        # Log Bench Press (Compound)
        bench_w = 40.0 + (60.0 * progress_factor) + random.uniform(-2, 2)
        log_lifting(ex_ids["Bench Press"], session_id, date_str, "compound", bench_w, 8)
        
        # Log Pull-ups (Bodyweight) - Reps increase instead of weight
        pullup_reps = int(5 + (10 * progress_factor) + random.randint(-1, 1))
        log_lifting(ex_ids["Pull-ups"], session_id, date_str, "bodyweight", 0.0, pullup_reps)
        
        # Log Bicep Curls (Isolation)
        curl_w = 10.0 + (15.0 * progress_factor) + random.uniform(-1, 1)
        log_lifting(ex_ids["Bicep Curls"], session_id, date_str, "isolation", curl_w, 12)
        
        # Log 5K Run (Running) - Time drops from ~35m to ~22m
        run_dist = 5.0
        run_time_sec = int(2100 - (780 * progress_factor) + random.randint(-60, 60))
        log_running(ex_ids["5K Run"], session_id, date_str, run_dist, run_time_sec)
        
        # Finish the session to trigger the RPG Engine
        r = session.post(f"{BASE_URL}/user/workouts/{workout_id}/finish", headers=headers, json={
            "duration_sec": 3600, # 1 hour sessions
            "session_id": session_id
        })
        
        workouts_completed += 1
        if workouts_completed % 20 == 0:
            print(f"   ... Completed {workouts_completed} workouts (Date simulated: {current_date.strftime('%Y-%m-%d')})")

    print_step(f"Simulation complete! {workouts_completed} total sessions logged.")

    # 6. FETCH FINAL RESULTS
    r = session.get(f"{BASE_URL}/user", headers=headers)
    user_data = r.json()
    print("==================================================")
    print(f"🏅 FINAL CHARACTER STATE:")
    print(f"   Level: {user_data.get('level')} | Total XP: {user_data.get('total_xp')}")
    print(f"   Highest Streak: {user_data.get('highest_streak')} Days")
    print(f"   Stats: {user_data.get('stats')}")
    print(f"   Trophies Unlocked: {len(user_data.get('achievements', []))}")
    print("==================================================")


def log_lifting(ex_id, session_id, date_str, type_str, weight, reps):
    # Simulate 3 sets, spaced out by 2 minutes to satisfy average_rest_sec math
    base_time = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    raw_sets = []
    
    for i in range(1, 4):
        set_time = base_time + datetime.timedelta(minutes=i*2)
        raw_sets.append({
            "set_number": i,
            "reps": reps,
            "weight": round(weight, 1),
            "completed_at": set_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "technique_rating": random.randint(3, 5) # 3 to 5 stars
        })
        
    session.post(f"{BASE_URL}/log_exercise", headers=headers, json={
        "exercise_id": ex_id,
        "session_id": session_id,
        "date": date_str,
        "log_type": type_str,
        "raw_data": {"raw_sets": raw_sets}
    })

def log_running(ex_id, session_id, date_str, dist_km, time_sec):
    session.post(f"{BASE_URL}/log_exercise", headers=headers, json={
        "exercise_id": ex_id,
        "session_id": session_id,
        "date": date_str,
        "log_type": "running",
        "raw_data": {"distance_km": dist_km, "time_sec": time_sec}
    })

if __name__ == "__main__":
    run_simulation()