import os
from dataclasses import dataclass


@dataclass(slots=True)
class BaseConfig:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me")
    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
    DEBUG: bool = os.getenv("FLASK_DEBUG", "0") == "1"

    # Spotify
    SPOTIFY_CLIENT_ID: str | None = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET: str | None = os.getenv("SPOTIFY_CLIENT_SECRET")
    SPOTIFY_REDIRECT_URI: str | None = os.getenv("SPOTIFY_REDIRECT_URI")

    # Firebase
    FIREBASE_PROJECT_ID: str | None = os.getenv("FIREBASE_PROJECT_ID")
    FIREBASE_CLIENT_EMAIL: str | None = os.getenv("FIREBASE_CLIENT_EMAIL")
    FIREBASE_PRIVATE_KEY: str | None = os.getenv("FIREBASE_PRIVATE_KEY")
    FIREBASE_DATABASE_URL: str | None = os.getenv("FIREBASE_DATABASE_URL")


class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True


class ProductionConfig(BaseConfig):
    DEBUG: bool = False


_CONFIG_MAP = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None) -> type[BaseConfig]:
    env_name = name or os.getenv("FLASK_ENV", "development").lower()
    return _CONFIG_MAP.get(env_name, DevelopmentConfig)
