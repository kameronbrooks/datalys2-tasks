from pydantic import BaseModel
import os
import json

class Settings(BaseModel):
    server_host: str = "127.0.0.1"
    server_port: int = 8000
    database_url: str = "" # Set in __init__ or defaulting

    def __init__(self, **data):
        super().__init__(**data)
        if not self.database_url:
            app_data = os.getenv('APPDATA') or os.path.expanduser('~')
            app_dir = os.path.join(app_data, 'datalys2-tasks')
            os.makedirs(app_dir, exist_ok=True)
            db_path = os.path.join(app_dir, 'datalys2.db')
            self.database_url = f"sqlite:///{db_path}"

    @classmethod
    def load(cls, config_path: str = "datalys_config.json") -> "Settings":
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = json.load(f)
                return cls(**data)
        return cls()

settings = Settings.load()
