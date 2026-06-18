from contextlib import asynccontextmanager

from fastapi import FastAPI
from database import engine, Base

import models.models  # noqa: F401

from routers import auth, boards, sections, tickets


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Trello REST API",
    description=(
        "A Trello-style project management REST API built with FastAPI and PostgreSQL.\n\n"
        "## Authentication\n"
        "1. **Register** a new account via `POST /auth/register`.\n"
        "2. **Login** via `POST /auth/login` to receive a Bearer JWT token.\n"
        "3. Click the **Authorize** button (🔒) above and paste the token to unlock all protected endpoints.\n\n"
        "## Permissions\n"
        "- **Board owner** can create/edit/delete sections and any ticket on the board.\n"
        "- **Invited members** can create tickets and only edit/delete their own tickets."
    ),
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(boards.router)
app.include_router(sections.router)
app.include_router(tickets.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Trello REST API is running 🚀"}
