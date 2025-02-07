from pydantic import BaseModel


class Config(BaseModel):
    """Plugin Config Here"""
    taygedo_helper_auto_sign_time: str = "08:30"
