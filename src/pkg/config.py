from pydantic import ConfigDict
from pydantic_settings import BaseSettings

CENTER_LAT = 49.0139
CENTER_LON = 31.4859
EARTH_RADIUS = 6371


class Settings(BaseSettings):
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    model_config = ConfigDict()


settings = Settings()
