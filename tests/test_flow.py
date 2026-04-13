import requests
import uuid
import json

# Test Funkcjonalny dla TrainingArc Server

# ADRES TWOJEGO SERWERA (Zmień jeśli testujesz lokalnie lub na VPS)
BASE_URL = "http://192.168.0.108:5000"

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

    # 1. REJESTRACJA
    payload = {"email": email, "password": password}
    r = session.post(f"{BASE_URL}/register", json=payload)
    if r.status_code == 201:
        print_pass("Rejestracja")
        # Token jest już tutaj zwracany, ale przetestujmy też login
    else:
        print_fail("Rejestracja", r)

    # 2. LOGIN
    r = session.post(f"{BASE_URL}/login", json=payload)
    if r.status_code == 200:
        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print_pass("Logowanie")
    else:
        print_fail("Logowanie", r)

    # 3. AKTUALIZACJA PROFILU (PATCH)
    payload = {"username": f"Tester_{unique_id}", "weight": 80.5}
    r = session.patch(f"{BASE_URL}/user", headers=headers, json=payload)
    if r.status_code == 200:
        print_pass("Aktualizacja profilu (PATCH)")
    else:
        print_fail("Aktualizacja profilu", r)

    # 4. TWORZENIE ĆWICZENIA (POST)
    payload = {"name": "Test Bench Press"}
    r = session.post(f"{BASE_URL}/user/exercises", headers=headers, json=payload)
    if r.status_code == 201:
        exercise_id = r.json().get("exercise_id")
        print_pass(f"Utworzono ćwiczenie (ID: {exercise_id})")
    else:
        print_fail("Tworzenie ćwiczenia", r)

    # 5. AKTUALIZACJA ĆWICZENIA (PATCH) - Ustawienie typu i celu
    payload = {
        "main_type": "freeweight",
        "notes": "Testowe notatki",
        "goal": "4x10 100kg"
    }
    r = session.patch(f"{BASE_URL}/user/exercises/{exercise_id}", headers=headers, json=payload)
    if r.status_code == 200:
        print_pass("Edycja ćwiczenia (PATCH)")
    else:
        print_fail("Edycja ćwiczenia", r)

    # 6. POBRANIE LISTY ĆWICZEŃ
    r = session.get(f"{BASE_URL}/user/exercises", headers=headers)
    exercises = r.json()
    if r.status_code == 200 and len(exercises) > 0:
        print_pass(f"Pobrano listę ćwiczeń (Znaleziono: {len(exercises)})")
    else:
        print_fail("Pobieranie ćwiczeń", r)

    # 7. LOGOWANIE TRENINGU (Smart Aggregation)
    payload = {
        "exercise_id": exercise_id,
        "log_type": "freeweight",
        "raw_data": {
            "raw_sets": [
                {"reps": 10, "weight": 100},
                {"reps": 8,  "weight": 105}
            ]
        }
    }
    r = session.post(f"{BASE_URL}/log_workout", headers=headers, json=payload)
    if r.status_code == 201:
        print_pass("Zalogowano trening")
    else:
        print_fail("Logowanie treningu", r)

    # 8. SPRAWDZENIE STATYSTYK
    r = session.get(f"{BASE_URL}/stats/{exercise_id}", headers=headers)
    if r.status_code == 200:
        stats = r.json() # To wraca jako string JSON w obecnym kodzie backendu
        print_pass("Pobrano statystyki")
        print(f"   🔍 Dane statystyk: {stats}")
    else:
        print_fail("Pobieranie statystyk", r)

    print("\n--- TEST ZAKOŃCZONY SUKCESEM ---")

if __name__ == "__main__":
    try:
        run_test()
    except requests.exceptions.ConnectionError:
        print("❌ Nie można połączyć się z serwerem. Czy na pewno działa?")