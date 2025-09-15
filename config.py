from dataclasses import dataclass
import os

@dataclass
class Config:
    bot_token: str
    admin: str
    mongo_uri: str 

def load_config():
    return Config(
        bot_token=os.getenv("BOT_TOKEN"),
        admin=os.getenv("ADMIN_ID"),
        mongo_uri=os.getenv("DBMONGO_URL"),
    )
