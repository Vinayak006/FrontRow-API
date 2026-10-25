from fastapi import FastAPI
from app.routers.main import main_router

app = FastAPI(title="FrontRow - Event Ticketing", version="1.0")


app.include_router(main_router)
