from pydantic import ConfigDict
from pydantic_settings import BaseSettings

CENTER_LAT = 49.0139
CENTER_LON = 31.4859


class Settings(BaseSettings):
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    LOG_FILE_NAME: str = "app"

    model_config = ConfigDict()


settings = Settings()
