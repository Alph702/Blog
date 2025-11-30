from flask import Flask
from config import Config
import blueprints
from utils.logger import setup_logging

app: Flask = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

main_logger = setup_logging(app, log_file=Config.LOG_FILE, level=Config().LOGGING_LEVEL)

# Register Blueprints
app.register_blueprint(blueprints.auth_bp)
app.register_blueprint(blueprints.blog_bp)
app.register_blueprint(blueprints.admin_bp)
app.register_blueprint(blueprints.api_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)