from flask import Blueprint, Flask

from .health_routes import health_bp
from .debug_routes import debug_bp
from .users_routes import users_bp
from .library_routes import library_bp
from .match_routes import match_bp
from .track_routes import tracks_bp
from .spotify_routes import spotify_bp
from .personality_routes import personality_bp
from .search_routes import search_bp

def register_routes(app: Flask) -> None:
    app.register_blueprint(health_bp)
    app.register_blueprint(debug_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(library_bp)
    app.register_blueprint(match_bp)
    app.register_blueprint(tracks_bp)
    app.register_blueprint(spotify_bp)
    app.register_blueprint(personality_bp)
    app.register_blueprint(search_bp)
    
    
    