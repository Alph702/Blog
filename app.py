from flask import Flask, helpers
import os
from config import Config
import blueprints
from utils.logger import setup_logging
import logging

app: Flask = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

main_logger = setup_logging(app, log_file=Config.LOG_FILE, level=Config().LOGGING_LEVEL)

# Module-level logger for app module
logger = logging.getLogger(__name__)
logger.info("Flask application initialized")

# Register Blueprints
app.register_blueprint(blueprints.auth_bp)
app.register_blueprint(blueprints.blog_bp)
app.register_blueprint(blueprints.admin_bp)
app.register_blueprint(blueprints.api_bp)


# Log unhandled exceptions with traceback
@app.errorhandler(Exception)
def handle_exception(e):
    main_logger.error(f"An unhandled exception occurred: {e}", exc_info=True)
    return "Internal Server Error", 500


@app.route("/favicon.ico")
def favicon():
    return helpers.send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
