import asyncpg
from helpers.config import get_settings, Settings


class BaseDataModel:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.app_settings = get_settings()
