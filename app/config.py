from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://pinelabs:pinelabs@localhost:5432/pinelabs"
    app_host: str = "0.0.0.0"
    app_port: int = 8000


settings = Settings()
