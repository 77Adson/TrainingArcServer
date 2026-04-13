import pytest
from app import create_app, mongo

# --- KONFIGURACJA ŚRODOWISKA TESTOWEGO ---
@pytest.fixture
def app():
    # Tworzymy aplikację z nadpisaną konfiguracją dla testów
    class TestConfig:
        TESTING = True
        # Używamy osobnej bazy testowej!
        MONGO_URI = "mongodb://localhost:27017/trainingarc_TEST_DB"
        JWT_SECRET_KEY = "test-secret-key"

    app = create_app(TestConfig)
    
    # Czyścimy bazę testową przed każdym testem
    with app.app_context():
        mongo.db.users.drop()
        mongo.db.exercises.drop()

    yield app

    # Czyścimy po teście
    with app.app_context():
        mongo.db.users.drop()
        mongo.db.exercises.drop()

@pytest.fixture
def client(app):
    return app.test_client()

# --- WŁAŚCIWE TESTY INTEGRACYJNE ---
class TestAuthAndUserIntegration:
    def test_register_and_login_flow(self, client):
        payload = {"email": "test@example.com", "password": "secure123"}
        
        # 1. Test Rejestracji
        response_reg = client.post("/register", json=payload)
        assert response_reg.status_code == 201
        assert "access_token" in response_reg.get_json()

        # 2. Rejestracja tego samego maila powinna zwrócić konflikt (409)
        response_reg_duplicate = client.post("/register", json=payload)
        assert response_reg_duplicate.status_code == 409

        # 3. Test Logowania
        response_login = client.post("/login", json=payload)
        assert response_login.status_code == 200
        token = response_login.get_json()["access_token"]
        assert token is not None

    def test_protected_route_access(self, client):
        # 1. Odmowa dostępu bez tokena
        response_no_auth = client.get("/user")
        assert response_no_auth.status_code == 401

        # 2. Utworzenie usera i uzyskanie tokena
        client.post("/register", json={"email": "auth@test.com", "password": "123"})
        login_res = client.post("/login", json={"email": "auth@test.com", "password": "123"})
        token = login_res.get_json()["access_token"]

        # 3. Dostęp przyznany z poprawnym tokenem
        response_auth = client.get("/user", headers={"Authorization": f"Bearer {token}"})
        assert response_auth.status_code == 200
        
        # Sprawdzamy czy backend załadował startowe atrybuty RPG zadeklarowane w rejestracji
        user_data = response_auth.get_json()
        assert user_data["level"] == 1
        assert user_data["stats"]["strength"] == 10

class TestExerciseIntegration:
    def test_create_exercise_and_retrieve(self, client):
        # Setup: Zaloguj testowego użytkownika
        client.post("/register", json={"email": "ex@test.com", "password": "123"})
        token = client.post("/login", json={"email": "ex@test.com", "password": "123"}).get_json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Tworzymy ćwiczenie
        create_res = client.post("/user/exercises", headers=headers, json={"name": "Deadlift"})
        assert create_res.status_code == 201
        exercise_id = create_res.get_json()["exercise_id"]

        # 2. Pobieramy listę i weryfikujemy czy ćwiczenie tam jest
        list_res = client.get("/user/exercises", headers=headers)
        assert list_res.status_code == 200
        exercises = list_res.get_json()
        
        assert len(exercises) == 1
        assert exercises[0]["name"] == "Deadlift"
        assert exercises[0]["_id"] == exercise_id
        
        # Sprawdzamy czy domyślne parametry RPG ćwiczenia zostały ustawione
        assert exercises[0]["stats"]["mastery"]["level"] == 1