from helpers.config import get_settings, Settings
import os
import random
import string
class BaseController:
    def __init__(self):
        self.app_settings = get_settings()
        #base directory get src path at current machine
        self.base_dir=os.path.dirname(os.path.dirname(__file__))
        self.files_dir=os.path.join(self.base_dir,"assets","files")
        
        
        self.database_dir=os.path.join(self.base_dir,"assets","database")
    
    
    def generate_random_string(self, length: int = 12):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def get_database_dir(self, database_name: str):
        database_dir=os.path.join(self.database_dir, database_name)
        if not os.path.exists(database_dir):
            os.makedirs(database_dir)
        return database_dir