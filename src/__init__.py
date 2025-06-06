import logging
import logging.config
import pathlib
import os

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.absolute()
log_dir = os.getenv("LOG_DIR", "/var/log/wrowfusion-dashboard")
os.makedirs(log_dir, exist_ok=True)

logger_config_path = str(PROJECT_ROOT / 'config' / 'logging.conf')
log_path = pathlib.Path(log_dir) / "wrowfusion-dashboard.log"
logging.config.fileConfig(str(logger_config_path), defaults={"log_path": str(log_path)}, disable_existing_loggers=False)
logger = logging.getLogger(__name__)

from flask import Flask
from src.routes import register_routes

logger = logging.getLogger(__name__)


def create_dashboard_app():
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates"
    )

    app.config['SECRET_KEY'] = os.getenv("WRFD_SECRET_KEY", "changeme")

    # Set backend API base URL. Note that this assumes that wrowfusion-dashboard is running on the 
    # same host as wrowfusion.
    api_scheme = os.getenv("WRFD_WROWFUSION_API_SCHEME", "http")
    api_host = os.getenv("WRFD_WROWFUSION_API_HOST", "127.0.0.1")
    api_port = os.getenv("WRFD_WROWFUSION_API_PORT", "5001")
    
    # NB: Do not include a trailing slash in the BACKEND_API string.
    app.config["BACKEND_API_URL"] = f"{api_scheme}://{api_host}:{api_port}/api"

    # Register routes
    register_routes(app)

    return app

app = create_dashboard_app()  # Gunicorn will use this
