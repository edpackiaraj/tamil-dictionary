"""
FastAPI main application — Tamil Dictionary API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.routers import search, words, community, admin, auth, morphology


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Professional Tamil Lexical Dictionary API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router,    prefix="/api", tags=["Search"])
app.include_router(words.router,     prefix="/api", tags=["Words"])
app.include_router(community.router, prefix="/api", tags=["Community"])
app.include_router(admin.router,     prefix="/admin", tags=["Admin"])
app.include_router(auth.router,       prefix="/api/auth",       tags=["Auth"])
app.include_router(morphology.router, prefix="/api",            tags=["Morphology"])


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "app": settings.app_name, "version": settings.version}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
