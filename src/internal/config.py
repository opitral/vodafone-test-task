from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    model_config = ConfigDict()


settings = Settings()
