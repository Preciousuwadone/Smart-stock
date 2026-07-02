from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.extensions import db, jwt, bcrypt

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    CORS(app)

    from app.auth.routes import auth_bp
    from app.customers.routes import customers_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(customers_bp)

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    return app