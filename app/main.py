# Purpose: This file creates and exposes the global FastAPI app instance

from fastapi import FastAPI
from app.api.v1.endpoints import router as api_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow React frontend to talk to FastAPI
origins = [
    "http://localhost:3000",
    "http://172.16.9.132:3000",   # or your frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # allow POST, GET, DELETE, etc.
    allow_headers=["*"],  # allow Content-Type
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ok"}