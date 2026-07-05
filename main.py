import os
import uvicorn

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.connection import Base, close_db, engine
from services.rag.rag_models import warm_up_embeddings_model
from services.routes import (
    company_auth,
    team_auth,
    team_register,
    knowledge,
    chat,
    company_dashboard,
    team_dashboard,
)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Load the embedding model eagerly so it is ready before the
    # first document upload or chat query arrives.
    import asyncio
    await asyncio.to_thread(warm_up_embeddings_model)

    yield
    await close_db()


app = FastAPI(
    title="IntelDocs AI",
    version="1.0.0",
    description="API for company, team, knowledge, and chat management",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(company_auth.router)
app.include_router(team_auth.router)
app.include_router(team_register.router)
app.include_router(knowledge.router)
app.include_router(chat.router)
app.include_router(company_dashboard.router)
app.include_router(team_dashboard.router)


@app.get("/")
async def root():
    return {"message": "IntelDocs AI API is running"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)