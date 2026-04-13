import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from locust import HttpUser, task, between
import uuid
import random
import datetime

class TrainingArcUser(HttpUser):
    # Domyślny adres hosta, aby uniknąć konieczności podawania flagi --host
    host = "http://192.168.0.108:5000/"
    wait_time = between(1, 3)
    token = None
    my_exercises = []
    my_workouts = []

    def on_start(self):
        unique_id = str(uuid.uuid4())[:8]
        email = f"stress_{unique_id}@test.com"
        password = "password123"

        self.client.post("/register", json={"email": email, "password": password})
        response = self.client.post("/login", json={"email": email, "password": password})
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
            
            # Przygotowanie danych testowych
            self.create_dummy_exercise("Bench Press")
            self.create_dummy_exercise("Squat")
            self.create_dummy_workout("Heavy Lifts")

    def create_dummy_exercise(self, name):
        if not self.token: return
        res = self.client.post("/user/exercises", headers=self.headers, json={"name": name})
        if res.status_code == 201:
            ex_id = res.json().get("exercise_id")
            # Ustawiamy od razu główny typ ćwiczenia
            self.client.patch(f"/user/exercises/{ex_id}", headers=self.headers, json={"main_type": "compound"})
            self.my_exercises.append(ex_id)

    def create_dummy_workout(self, name):
        if not self.token: return
        res = self.client.post("/user/workouts", headers=self.headers, json={"name": name})
        if res.status_code == 201:
            workout_id = res.json().get("workout_id")
            self.my_workouts.append(workout_id)

    @task(3)
    def view_profile(self):
        if self.token:
            self.client.get("/user", headers=self.headers)

    @task(5)
    def list_exercises(self):
        if self.token:
            self.client.get("/user/exercises", headers=self.headers)

    @task(2)
    def log_exercise_and_finish_workout(self):
        """Symuluje pełny obieg: wykonanie ćwiczenia i sporadyczne zakończenie treningu."""
        if self.token and self.my_exercises and self.my_workouts:
            exercise_id = random.choice(self.my_exercises)
            workout_id = random.choice(self.my_workouts)
            session_id = str(uuid.uuid4())
            
            base_time = datetime.datetime.now(datetime.timezone.utc)
            date_str = base_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Generowanie 3 serii z 2-minutowymi przerwami
            raw_sets = []
            for i in range(1, 4):
                set_time = base_time + datetime.timedelta(minutes=i*2)
                raw_sets.append({
                    "set_number": i,
                    "reps": random.randint(5, 12),
                    "weight": float(random.randint(60, 100)),
                    "completed_at": set_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "technique_rating": random.randint(3, 5)
                })
            
            payload = {
                "exercise_id": exercise_id,
                "session_id": session_id,
                "date": date_str,
                "log_type": "compound",
                "raw_data": {
                    "raw_sets": raw_sets
                }
            }
            
            # Logowanie ćwiczenia
            self.client.post("/log_exercise", headers=self.headers, json=payload)
            
            # 30% szans, że użytkownik od razu zamyka trening
            if random.random() < 0.3:
                self.client.post(f"/user/workouts/{workout_id}/finish", headers=self.headers, json={
                    "duration_sec": random.randint(1800, 5400),
                    "session_id": session_id
                })

# Pozwala na uruchomienie skryptu bezpośrednio (np. przyciskiem Run w VS Code)
if __name__ == "__main__":
    os.system(f"locust -f {__file__}")