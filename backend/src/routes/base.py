from fastapi import FastAPI, APIRouter, Depends
from helpers.config import get_settings, Settings
base_router = APIRouter(
    prefix="/api/v1",
# tags is for the documentation
    tags=["base"]
)
@base_router.get("/")
async def welcome(app_settings: Settings = Depends(get_settings)):
    return {"message": f"Welcome to  {app_settings.APP_NAME} version {app_settings.APP_VERSION} by {app_settings.APP_AUTHOR}"}