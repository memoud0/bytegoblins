from .debug_routes import debug_bp

def register_routes(app):
    app.register_blueprint(debug_bp)
    # register other blueprints...
