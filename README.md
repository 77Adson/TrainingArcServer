# TrainingArc Server

Backend API for the **TrainingArc** app — a gamified workout tracker where logging real training sessions earns XP, levels, RPG-style stats, and achievements. Built with Flask, MongoDB, and JWT authentication.

This is the **`Local-hosting`** branch: it's set up to run fully locally via Docker Compose, bundling its own MongoDB container instead of depending on an external/cloud database.

Companion client app: [TrainingArc2Client](https://github.com/77Adson/TrainingArc2Client) (native Android, Kotlin + Jetpack Compose).

## Table of contents

- [Features](#features)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Data model](#data-model)
- [Setup](#setup)
  - [Option A: Docker Compose (recommended)](#option-a-docker-compose-recommended)
  - [Option B: Local Python environment](#option-b-local-python-environment)
- [Configuration (environment variables)](#configuration-environment-variables)
- [Seeding achievements](#seeding-achievements)
- [API documentation](#api-documentation)
- [Tests](#tests)
- [Connecting the Android client](#connecting-the-android-client)

## Features

- **Auth** — registration/login with bcrypt-hashed passwords and JWT access tokens (7-day expiry).
- **RPG progression system** — every user has a level, total XP, and five stats (`strength`, `stamina`, `dexterity`, `endurance`, `consistency`) that grow from real workout data. Each exercise has its own sub-stats (`mastery`, `strength`, `stamina`, `momentum`).
- **Smart workout logging** — `POST /log_exercise` accepts raw sets (or run data) and the server computes volume, estimated 1RM (Epley formula), average rest time, and a "momentum" score comparing the session to your recent history.
- **Achievements** — a database-driven achievement system (level milestones, stat-tier "ranks" à la League of Legends, and fun/grind milestones), evaluated automatically after each finished workout.
- **Streaks** — an adherence-based streak calculated against your own scheduled workout days, not just "any activity."
- **Dashboard** — weekly schedule, today's workout, streak/progress stats, and recent achievements in a single call.
- **Workout blueprints** — create reusable workout plans, organize exercises into groups, assign days of the week, and track completion count / average duration.
- **Social / friends** — add friends via a short-lived signed QR invite token, view friends' RPG profiles, browse and clone their workout blueprints (with personal notes/tags stripped out).
- **Offline-friendly logging** — `log_exercise` is an upsert keyed by `session_id`, so a client can safely retry/resend a session's data.
- Unit tests, integration tests, an end-to-end functional test, a full year-long usage simulation, and a Locust load test.

## Tech stack

| Layer | Technology |
|---|---|
| Web framework | Flask 3.1 |
| Database | MongoDB (via Flask-PyMongo) |
| Authentication | Flask-JWT-Extended (JWT) |
| Password hashing | Flask-Bcrypt |
| Production server | Gunicorn |
| Containerization | Docker / Docker Compose (app + MongoDB) |
| Testing | Pytest (unit + integration), Locust (load) |

## Project structure

```
app/
  auth/
    routes.py                 # Register / login
  main/
    api/
      dashboard_routes.py       # GET /user/dashboard
      exercise_routes.py        # CRUD for exercises
      exercise_log_routes.py    # POST /log_exercise, exercise stats/history
      social_routes.py          # Friends: invite, scan, list, profile, workouts
      user_routes.py            # User profile, achievements list
      workout_routes.py         # Workout blueprints, finish/clone
  repositories/                 # Thin MongoDB access layer, one file per collection
  services/
    achievements.py             # Achievement evaluation logic
    dashboard_service.py        # Weekly schedule + streak calculation
    rpg_engine.py                # Orchestrates XP/level/achievement processing after a workout
    rpg_math.py                  # Pure XP/level/momentum math
    social_service.py            # Workout blueprint cloning
    workout_processor.py         # Smart Aggregation (volume, e1RM, rest time)
DBscripts/
  seed_achivements.py           # One-off script to populate the achievements collection
tests/
  conftest.py                   # Test JWT secret setup
  test_unit.py                  # Pure math/logic tests
  test_integration.py           # Flask test client, in-process API tests
  test_flow.py                  # End-to-end functional test against a running server
  test_year_simulation.py       # Simulates a full year of workouts against a running server
  locustfile.py                 # Load test
config.py                       # Env-driven configuration
docker-compose.yml              # App + bundled MongoDB container
Dockerfile
requirements.txt
run.py                          # Entry point
```

## Data model

MongoDB collections used by the server:

- **`users`** — `email`, `hashed_password`, `username`, `weight`, `preferences`, `level`, `total_xp`, `highest_streak`, `achievements` (list of IDs), `stats` (`strength`, `stamina`, `dexterity`, `endurance`, `consistency`), `created_at`.
- **`exercises`** — `userId`, `name`, `main_type`, `tags`, `goal`, `weight`, `current_tempo_stats`, `technique_rating`, `notes`, `links`, `image_paths`, `progression_mode`, `stats` (`mastery`, `strength`, `stamina`, `momentum`, each `{level, xp}`).
- **`workouts`** — `userId`, `name`, `description`, `days_of_week`, `exercise_groups`, `average_time_sec`, `sessions_completed`, `created_at`.
- **`exercise_logs`** — `userId`, `exercise_id`, `session_id`, `date`, `log_type` (`compound` / `isolation` / `bodyweight` / `running`), aggregated fields (`aggr_total_volume`, `aggr_best_e1RM`, `aggr_average_rest_sec`, `aggr_total_distance_km`, `aggr_total_time_sec`) and raw input (`raw_sets`, etc.).
- **`friendships`** — `user1`, `user2`, `created_at`.
- **`achievements`** — `_id` (slug), `name`, `description`, optional `stat_requirement: {stat, value}` for tiered stat achievements.

## Setup

### Option A: Docker Compose (recommended)

This branch's `docker-compose.yml` runs **both** the Flask server and a MongoDB container, so there's nothing extra to install besides Docker.

```bash
git clone https://github.com/77Adson/TrainingArcServer.git
cd TrainingArcServer
git checkout Local-hosting
```

1. Create a `.env` file in the project root (see [Configuration](#configuration-environment-variables)):

   ```env
   JWT_SECRET_KEY=change-me-to-a-real-secret
   FLASK_DEBUG=false
   ```

2. Start everything:

   ```bash
   docker compose up --build
   ```

   This brings up:
   - `trainingarc_db` — MongoDB, exposed on `27017`, with a named volume (`mongo_data`) so data survives restarts.
   - `trainingarc_server` — the Flask API via Gunicorn, exposed on `5000`, already pointed at the MongoDB container (`MONGO_URI=mongodb://mongodb:27017/trainingarc` is set automatically in `docker-compose.yml`).

3. Seed the achievements collection once (see [Seeding achievements](#seeding-achievements)).

### Option B: Local Python environment

Requirements: Python 3.12+, a MongoDB instance running locally (e.g. `docker run -p 27017:27017 mongo` or a local install).

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Set the environment variables from the [Configuration](#configuration-environment-variables) section (or create a `.env` and export it), then:

```bash
python run.py
```

The server starts on `http://0.0.0.0:5000`.

## Configuration (environment variables)

| Variable | Description | Default |
|---|---|---|
| `MONGO_URI` | MongoDB connection string | `mongodb://localhost:27017/trainingarc` |
| `JWT_SECRET_KEY` | Secret used to sign JWT tokens | `dev-secret-key` |
| `FLASK_DEBUG` | `true`/`false` — enables Flask debug mode | `True` |

`config.py` includes a safety check: if `JWT_SECRET_KEY` is still `dev-secret-key` **and** `FLASK_DEBUG` is not truthy, the app refuses to start:

```python
if JWT_SECRET_KEY == "dev-secret-key" and not DEBUG:
    raise ValueError("CRITICAL ERROR: Lack of JWT_SECRET_KEY in environment variables. Please set it before running the server in production.")
```

This prevents accidentally deploying with a public, guessable JWT secret — always set a real `JWT_SECRET_KEY` before disabling debug mode.

> **Note:** keep real secrets in a `.env` file and never commit it. `.gitignore` currently excludes `.env/` (a *directory* named `.env`); if you create a plain `.env` *file* instead (as `docker-compose.yml`'s `env_file: .env` expects), double-check it's actually being ignored by git before committing.

## Seeding achievements

The achievement definitions live in the database, not in code, so they need to be seeded once:

```bash
python DBscripts/seed_achivements.py
```

This connects to `mongodb://localhost:27017/` and populates the `trainingarc.achievements` collection (core milestones, a five-stat/nine-tier "ranked" ladder, and a handful of fun/grind achievements). If you're running MongoDB inside Docker Compose, run this script from the host (with the container's port `27017` published, which it is by default) rather than from inside the `web` container.

## API documentation

All endpoints except `/register` and `/login` require:

```
Authorization: Bearer <access_token>
```

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/register` | Registers a user and returns an `access_token`; initializes level 1, 0 XP, and base RPG stats |
| POST | `/login` | Logs in and returns an `access_token` |

### User

| Method | Endpoint | Description |
|---|---|---|
| GET | `/user` | Returns the logged-in user's profile, level, XP, stats, and achievements |
| PATCH | `/user` | Updates `username`, `weight`, and/or `preferences` |
| GET | `/achievements` | Lists all achievement definitions available in the game |

### Dashboard

| Method | Endpoint | Description |
|---|---|---|
| GET | `/user/dashboard` | Weekly schedule, today's workout, streak/progress stats, recent achievements |

### Exercises

| Method | Endpoint | Description |
|---|---|---|
| GET | `/user/exercises` | Lists the user's exercises |
| POST | `/user/exercises` | Creates a new exercise (`name` required) |
| GET | `/user/exercises/<exercise_id>` | Exercise details |
| PATCH | `/user/exercises/<exercise_id>` | Updates selected fields |
| DELETE | `/user/exercises/<exercise_id>` | Deletes an exercise |
| GET | `/user/exercises/<exercise_id>/stats` | Daily-aggregated history (volume, e1RM, max weight, rest time, distance/time) for charts |

### Exercise logs

| Method | Endpoint | Description |
|---|---|---|
| POST | `/log_exercise` | Upserts a log for one exercise within a session (`exercise_id`, `session_id`, `raw_data` required); computes aggregates server-side |

`log_type` accepts `compound`, `isolation`, `bodyweight`, or `running`. Example:

```json
{
  "exercise_id": "665f1a2b3c4d5e6f7a8b9c0d",
  "session_id": "c1a2b3c4-d5e6-7a8b-9c0d-1e2f3a4b5c6d",
  "date": "2026-09-27T10:00:00Z",
  "log_type": "compound",
  "raw_data": {
    "raw_sets": [
      { "set_number": 1, "reps": 10, "weight": 100, "completed_at": "2026-09-27T10:02:00Z", "technique_rating": 4 },
      { "set_number": 2, "reps": 8,  "weight": 105, "completed_at": "2026-09-27T10:04:00Z", "technique_rating": 3 }
    ]
  }
}
```

### Workouts

| Method | Endpoint | Description |
|---|---|---|
| GET | `/user/workouts` | Lightweight list of the user's workout plans |
| POST | `/user/workouts` | Creates a new empty workout blueprint (`name` required) |
| GET | `/user/workouts/<workout_id>` | Full blueprint (owner view, includes notes/schedule) |
| PATCH | `/user/workouts/<workout_id>` | Updates `name`, `description`, `days_of_week`, `exercise_groups` |
| DELETE | `/user/workouts/<workout_id>` | Deletes a workout plan |
| POST | `/user/workouts/<workout_id>/finish` | Ends a session: updates average duration/completion count and triggers the RPG engine (XP, level-ups, achievements) |
| POST | `/user/workouts/<workout_id>/clone` | Deep-clones a friend's blueprint (and its exercises) into the caller's library, resetting RPG progress |

### Social

| Method | Endpoint | Description |
|---|---|---|
| GET | `/friends/invite` | Generates a signed invite token (valid 10 minutes) to embed in a QR code |
| POST | `/friends/scan` | Redeems a scanned invite token and creates a friendship |
| GET | `/friends` | Lists friends with basic RPG stats |
| GET | `/friends/<friend_id>/profile` | Full RPG profile of a friend (requires an existing friendship) |
| GET | `/friends/<friend_id>/workouts` | Friend's sanitized workout blueprints (requires an existing friendship) |
| GET | `/friends/workouts/<workout_id>` | Sanitized view of one friend's blueprint (requires an existing friendship) |

## Tests

```bash
pip install pytest
pytest
```

- `test_unit.py` — pure math (e1RM, XP/level progression, technique multiplier), no database needed.
- `test_integration.py` — spins up the Flask app with a dedicated `trainingarc_TEST_DB` database and drops it before/after each test.
- `conftest.py` sets a fixed `JWT_SECRET_KEY` for the test session automatically.

Against a **running server** (update `BASE_URL` in each file if needed):

```bash
python tests/test_flow.py             # end-to-end smoke test
python tests/test_year_simulation.py  # simulates ~365 days of workouts to sanity-check XP/streaks/achievements at scale
```

Load test:

```bash
locust -f tests/locustfile.py
```

`locustfile.py` sets a default `host`, so you can start Locust without passing `--host` — just update the hardcoded address to match your environment first.

## Connecting the Android client

To use [TrainingArc2Client](https://github.com/77Adson/TrainingArc2Client) against this server:

1. Start the server (Docker Compose or local Python, above) — it listens on port `5000`.
2. In the client's `RetrofitClient.kt`, set `BASE_URL` to an address your phone/emulator can reach:
   - Physical device on the same Wi-Fi: your computer's LAN IP, e.g. `http://192.168.1.42:5000/`.
   - Android Emulator: `http://10.0.2.2:5000/` (routes to the host's `localhost`).
3. Rebuild and run the app, then register a new account from its Register screen.

See the [client README](https://github.com/77Adson/TrainingArc2Client#readme) for full client-side setup instructions.
