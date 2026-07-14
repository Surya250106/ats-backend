from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Database Settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "ats_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"

    # Queue Settings
    QUEUE_URL: str = "redis://localhost:6379/0"

    # Security Settings
    JWT_SECRET: str = "super_secret_jwt_signing_key_change_me_in_production_1234567890"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
