from flask import Flask
from config import Config
import blueprints

app: Flask = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Register Blueprints
app.register_blueprint(blueprints.auth_bp)
app.register_blueprint(blueprints.blog_bp)
app.register_blueprint(blueprints.admin_bp)
app.register_blueprint(blueprints.api_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)