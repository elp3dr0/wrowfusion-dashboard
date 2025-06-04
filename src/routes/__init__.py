from flask import Flask
from src.routes import users, rowing

def register_routes(app: Flask) -> None:
    app.register_blueprint(users.users_bp)
    app.register_blueprint(rowing.rowing_bp)