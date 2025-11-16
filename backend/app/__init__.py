from flask import Flask
from flask_cors import CORS

from .config import get_config
from .firebase_client import init_firebase_app
from .routes import register_routes


def create_app(config_name: str | None = None) -> Flask:
    """Application factory so tests and CLI share consistent setup."""
    app = Flask(__name__)

    # get_config currently returns a class (DevelopmentConfig / ProductionConfig)
    config_cls = get_config(config_name)
    app_config = config_cls()  # <-- instantiate it

    app.config.from_object(app_config)

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    init_firebase_app(app)
    register_routes(app)

    return app
