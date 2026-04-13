import requests
import uuid
import datetime

# Test Funkcjonalny dla TrainingArc Server
BASE_URL = "http://127.0.0.1:5000" # Zmień na swój adres IP / localhost

def print_pass(message):
    print(f"✅ PASS: {message}")

def print_fail(message, response=None):
    print(f"❌ FAIL: {message}")
    if response:
        print(f"   Status: {response.status_code}")
        print(f"   Body: {response.text}")
    exit(1)

def run_test():
    session = requests.Session()
    unique_id = str(uuid.uuid4())[:8]
    email = f"user_{unique_id}@test.com"
    password = "password123"

    print(f"--- Rozpoczynanie testu dla: {email} ---")

    # 1. REJESTRACJA & LOGIN
    session.post(f"{BASE_URL}/register", json={"email": email, "password": password})
    r = session.post(f"{BASE_URL}/login", json={"email": email, "password": password})
    if r.status_code == 200:
        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print_pass("Rejestracja i Logowanie")
    else:
        print_fail("Logowanie", r)

    # 2. TWORZENIE ĆWICZENIA
    r = session.post(f"{BASE_URL}/user/exercises", headers=headers, json={"name": "Test Bench Press"})
    if r.status_code == 201:
        exercise_id = r.json().get("exercise_id")
        print_pass(f"Utworzono ćwiczenie (ID: {exercise_id})")
    else:
        print_fail("Tworzenie ćwiczenia", r)

    # 3. AKTUALIZACJA ĆWICZENIA
    session.patch(f"{BASE_URL}/user/exercises/{exercise_id}", headers=headers, json={
        "main_type": "compound",
        "goal": "4x10 100kg"
    })

    # 4. TWORZENIE PLANU TRENINGOWEGO
    r = session.post(f"{BASE_URL}/user/workouts", headers=headers, json={"name": "Testowy Plan"})
    if r.status_code == 201:
        workout_id = r.json().get("workout_id")
        print_pass(f"Utworzono plan treningowy (ID: {workout_id})")
    else:
        print_fail("Tworzenie planu", r)

    # 5. LOGOWANIE TRENINGU (Poprawiony format czasu i wagi)
    session_id = str(uuid.uuid4())
    base_time = datetime.datetime.now(datetime.timezone.utc)
    
    # Sztuczne opóźnienia, aby backend mógł poprawnie wyliczyć "average_rest_sec"
    time_set_1 = (base_time + datetime.timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    time_set_2 = (base_time + datetime.timedelta(minutes=4)).strftime("%Y-%m-%dT%H:%M:%SZ")
    date_str = base_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    payload = {
        "exercise_id": exercise_id,
        "session_id": session_id,
        "date": date_str,
        "log_type": "compound",
        "raw_data": {
            "raw_sets": [
                {"set_number": 1, "reps": 10, "weight": 100.0, "completed_at": time_set_1, "technique_rating": 4},
                {"set_number": 2, "reps": 8,  "weight": 105.0, "completed_at": time_set_2, "technique_rating": 3}
            ]
        }
    }
    r = session.post(f"{BASE_URL}/log_exercise", headers=headers, json=payload)
    if r.status_code == 201:
        print_pass("Zalogowano ćwiczenie (log_exercise)")
    else:
        print_fail("Logowanie ćwiczenia", r)

    # 6. ZAKOŃCZENIE SESJI (Wyzwalacz RPG)
    r = session.post(f"{BASE_URL}/user/workouts/{workout_id}/finish", headers=headers, json={
        "duration_sec": 3600,
        "session_id": session_id
    })
    if r.status_code == 200:
        rpg_data = r.json()
        print_pass(f"Zakończono sesję. Zdobyto XP: {rpg_data.get('user_xp_gained')}")
    else:
        print_fail("Kończenie sesji", r)

    print("\n--- TEST ZAKOŃCZONY SUKCESEM ---")

if __name__ == "__main__":
    try:
        run_test()
    except requests.exceptions.ConnectionError:
        print("❌ Nie można połączyć się z serwerem. Czy na pewno działa?")