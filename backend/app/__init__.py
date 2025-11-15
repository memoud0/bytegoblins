from flask import Flask

from .blueprints import register_blueprints
from .config import get_config
from .services.firebase_service import init_firebase_app


def create_app(config_name: str | None = None) -> Flask:
    """Application factory so tests and CLI share consistent setup."""
    app = Flask(__name__)
    app_config = get_config(config_name)
    app.config.from_object(app_config)

    init_firebase_app(app)
    register_blueprints(app)

    return app
