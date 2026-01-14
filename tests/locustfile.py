from locust import HttpUser, task, between
import uuid
import random

# Test wydajnościowy dla TrainingArc Server

class TrainingArcUser(HttpUser):
    # Czas oczekiwania między akcjami symuluje myślenie użytkownika (1-3 sekundy)
    wait_time = between(1, 3)
    token = None
    my_exercises = []

    def on_start(self):
        """Uruchamiane raz dla każdego symulowanego użytkownika przy starcie"""
        unique_id = str(uuid.uuid4())[:8]
        email = f"stress_{unique_id}@test.com"
        password = "password123"

        # Rejestracja
        self.client.post("/register", json={"email": email, "password": password})
        
        # Logowanie i pobranie tokena
        response = self.client.post("/login", json={"email": email, "password": password})
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        
            # Tworzymy wstępnie 2 ćwiczenia, żeby mieć na czym pracować
            self.create_dummy_exercise("Bench Press")
            self.create_dummy_exercise("Squat")

    def create_dummy_exercise(self, name):
        if not self.token: return
        res = self.client.post("/user/exercises", headers=self.headers, json={"name": name})
        if res.status_code == 201:
            ex_id = res.json().get("exercise_id")
            self.my_exercises.append(ex_id)

    @task(3) # Weight 3 - użytkownik robi to częściej
    def view_profile(self):
        if self.token:
            self.client.get("/user", headers=self.headers)

    @task(5) # Weight 5 - użytkownik bardzo często odświeża listę ćwiczeń
    def list_exercises(self):
        if self.token:
            self.client.get("/user/exercises", headers=self.headers)

    @task(1) # Weight 1 - rzadziej tworzy nowe ćwiczenia
    def add_exercise(self):
        if self.token:
            name = f"Exercise {random.randint(1, 1000)}"
            self.create_dummy_exercise(name)

    @task(2) # Weight 2 - logowanie treningu
    def log_workout(self):
        if self.token and self.my_exercises:
            # Wybierz losowe ćwiczenie
            exercise_id = random.choice(self.my_exercises)
            payload = {
                "exercise_id": exercise_id,
                "log_type": "freeweight",
                "raw_data": {
                    "raw_sets": [
                        {"reps": random.randint(5, 12), "weight": random.randint(60, 100)}
                    ]
                }
            }
            self.client.post("/log_workout", headers=self.headers, json=payload)