from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.main import main_router

app = FastAPI(title="FrontRow - Event Ticketing", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(main_router)
