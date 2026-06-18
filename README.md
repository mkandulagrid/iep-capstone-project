# Trello REST API

A Trello-style project management REST API built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**. It provides Kanban-board functionality — boards, sections, tickets, user authentication, and invitation-based collaboration — through a clean, documented HTTP API.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| ORM | [SQLAlchemy](https://www.sqlalchemy.org/) |
| Database | PostgreSQL (production) / SQLite (tests) |
| Auth | JWT via [python-jose](https://github.com/mpdavis/python-jose), passwords hashed with [bcrypt](https://github.com/pyca/bcrypt/) |
| Validation | [Pydantic v2](https://docs.pydantic.dev/) |
| Testing | [pytest](https://pytest.org/), [pytest-cov](https://pytest-cov.readthedocs.io/), [httpx](https://www.python-httpx.org/) |

---

## Prerequisites

- Python **3.9+**
- PostgreSQL **13+** running locally
- `pip` / `virtualenv`

---

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd "iep capstone project"
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate      # macOS / Linux
# venv\Scripts\activate       # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the database

Create the PostgreSQL database:

```bash
psql -U postgres -c "CREATE DATABASE iep_capstone_project;"
```

Edit the `.env` file in the project root with your credentials:

```env
DRIVERNAME=postgresql+psycopg2
HOST=127.0.0.1
NAME=iep_capstone_project
USERNAME=postgres
PASSWORD=postgres
```

### 5. Run the API

```bash
cd app
uvicorn main:app --reload
```

The server will start at **http://127.0.0.1:8000**.  
All database tables are created automatically on first startup.

---

## API Documentation

Interactive Swagger UI is available at: **http://127.0.0.1:8000/docs**

Use the **Authorize** 🔒 button to paste your JWT token and unlock protected endpoints.

### Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/` | ❌ | Health check |
| POST | `/auth/register` | ❌ | Register a new user |
| POST | `/auth/login` | ❌ | Login → returns JWT Bearer token |
| POST | `/boards` | ✅ | Create a board |
| GET | `/boards` | ✅ | List user's boards |
| GET | `/boards/{id}` | ✅ | Board detail (sections, tickets, members, token) |
| POST | `/boards/{id}/invite` | ✅ Owner | Generate invitation token |
| POST | `/boards/join/{token}` | ✅ | Join a board via invitation token |
| POST | `/sections` | ✅ Owner | Create a section |
| GET | `/sections/{id}` | ✅ Member | Get section with tickets |
| PUT | `/sections/{id}` | ✅ Owner | Update section name/description |
| DELETE | `/sections/{id}` | ✅ Owner | Delete section (cascades tickets) |
| POST | `/tickets` | ✅ Member | Create a ticket |
| GET | `/tickets/{id}` | ✅ Member | Get ticket |
| PUT | `/tickets/{id}` | ✅ See rules | Update ticket |
| DELETE | `/tickets/{id}` | ✅ See rules | Delete ticket |

**Ticket permission rules:**
- Board **owner** → can edit/delete any ticket
- Invited **member** → can only edit/delete tickets they created

---

## Testing

### How the test environment works

Tests use a dedicated **PostgreSQL test database** (`iep_capstone_project_test`) with the same credentials as the main app (read from `.env`). This keeps test data completely separate from your production data.

Before running tests, create the test database once:

```bash
PGPASSWORD=postgres psql -U postgres -h 127.0.0.1 -c "CREATE DATABASE iep_capstone_project_test;"
```

The test suite automatically creates all tables before each test and drops them after, so every test starts with a clean, empty database.

### Setup

Make sure you have installed the dependencies (including test tools):

```bash
pip install -r requirements.txt
```

This installs `pytest`, `pytest-cov`, and `httpx` along with the application dependencies.

### Running the tests

From the **project root** (the directory containing `pytest.ini`):

```bash
# Run all tests
venv/bin/pytest

# Run with verbose output
venv/bin/pytest -v

# Run with coverage report
venv/bin/pytest --cov=app --cov-report=term-missing -v

# Run only unit tests
venv/bin/pytest tests/unit/ -v

# Run only integration tests
venv/bin/pytest tests/integration/ -v

# Run a specific test file
venv/bin/pytest tests/unit/test_auth_utils.py -v

# Run a specific test class or case
venv/bin/pytest tests/integration/test_auth.py::TestLogin::test_login_success_returns_200_and_token -v
```

### Test structure

```
tests/
├── conftest.py                      # Shared fixtures (DB, client, users, boards)
├── unit/
│   └── test_auth_utils.py           # Unit tests for utils/auth.py (21 cases)
└── integration/
    ├── test_auth.py                 # /auth/register + /auth/login (10 cases)
    ├── test_boards.py               # /boards CRUD + invite + join (17 cases)
    ├── test_sections.py             # /sections CRUD (15 cases)
    └── test_tickets.py              # /tickets CRUD + permissions (18 cases)
```

**Total: 81 test cases**

### Coverage targets

| Category | Covered | Requirement |
|---|---|---|
| Utility functions (`utils/auth.py`) | 4 / 4 = **100%** | ≥ 50% ✅ |
| API endpoints | 13 / 16 = **81%** | ≥ 50% ✅ |

---

## Project Structure

```
.
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── database.py              # SQLAlchemy engine + session factory
│   ├── models/
│   │   └── models.py            # ORM models (User, Board, BoardMember,
│   │                            #   InvitationToken, Section, Ticket)
│   ├── schemas/
│   │   ├── user.py
│   │   ├── board.py
│   │   ├── section.py
│   │   └── ticket.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── boards.py
│   │   ├── sections.py
│   │   └── tickets.py
│   └── utils/
│       ├── auth.py              # Password hashing + JWT helpers
│       └── dependencies.py     # get_current_user FastAPI dependency
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── .env                         # Database credentials (not committed)
├── requirements.txt
├── pytest.ini
└── README.md
```
