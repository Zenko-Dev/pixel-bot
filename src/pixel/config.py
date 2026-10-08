import os
from dataclasses import dataclass

VALID_ENVS = ("staging", "prod")

@dataclass(frozen=True)
class Settings:
    env: str
    token:str
    staging_channel_id: int
    error_channel_id: int
    welcome_channel_id: int

    @property
    def is_prod(self) -> bool:
        return self.env == "prod"

def _get_int(name: str) -> int:
    return int(os.getenv(name, "0"))

def load_settings() -> Settings:
    env = os.getenv("APP_ENV", "staging").lower()
    if env not in VALID_ENVS:
        raise RuntimeError(f"APP_ENV debe ser uno de {VALID_ENVS}, no '{env}'")
    
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("Falta DISCORD_TOKEN en el archivo .env")

    return Settings(
        env=env,
        token=token,
        staging_channel_id=_get_int("STAGING_CHANNEL_ID"),
        error_channel_id=_get_int("ERROR_CHANNEL_ID"),
        welcome_channel_id=_get_int("WELCOME_CHANNEL_ID"),
    )