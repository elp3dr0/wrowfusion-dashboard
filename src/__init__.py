import logging
import logging.config
import pathlib
import os

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.absolute()

log_dir = PROJECT_ROOT / 'logs'
os.makedirs(log_dir, exist_ok=True)

loggerconfigpath = str(PROJECT_ROOT / 'config' / 'logging.conf')
log_path = str(log_dir / "wrowfusion-dashboard.log")
logging.config.fileConfig(loggerconfigpath, defaults={"log_path": log_path}, disable_existing_loggers=False)
logger = logging.getLogger(__name__)

from flask import Blueprint, Flask
from dotenv import load_dotenv
from src.routes import register_routes

logger = logging.getLogger(__name__)

load_dotenv()

def create_dashboard_app():
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates"
    )

    app.config['SECRET_KEY'] = os.environ.get("WRFD_SECRET_KEY", "changeme")

    # Set backend API base URL. Note that this assumes that wrowfusion-dashboard is running on the 
    # same host as wrowfusion.
    api_scheme = os.environ.get("WRFD_WROWFUSION_API_SCHEME", "http")
    api_host = os.environ.get("WRFD_WROWFUSION_API_HOST", "127.0.0.1")
    api_port = os.environ.get("WRFD_WROWFUSION_API_PORT", "5001")
    
    # NB: Do not include a trailing slash in the BACKEND_API string.
    app.config["BACKEND_API_URL"] = f"{api_scheme}://{api_host}:{api_port}/api"

    # Register routes
    register_routes(app)

    return app

app = create_dashboard_app()  # Gunicorn will use this
