from contextlib import asynccontextmanager

from fastapi import FastAPI

from database.connection import Base, close_db, engine
from services.routes import company_auth, knowledge, team_auth, team_register


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await close_db()


app = FastAPI(
    title="IntelDocs AI",
    version="1.0.0",
    description="API for company, team, and knowledge management",
    lifespan=lifespan,
)

app.include_router(company_auth.router)
app.include_router(team_auth.router)
app.include_router(team_register.router)
app.include_router(knowledge.router)


@app.get("/")
async def root():
    return {"message": "IntelDocs AI API is running"}
