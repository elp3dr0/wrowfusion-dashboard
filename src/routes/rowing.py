from flask import Blueprint, request, redirect, url_for, render_template, session, current_app
import requests
import os
from src.utils.backend_api import get_user_from_backend

rowing_bp = Blueprint("rowing", __name__)

@rowing_bp.route("/rowing")
def show_rowing_page():
    websocket_port = os.getenv("WRFD_WROWFUSION_WEBSOCKET_PORT", 8765)

    user_id_raw = session.get("user_id")
    if not user_id_raw:
        cookie_user_id = request.cookies.get("stay_logged_in_user_id")
        if cookie_user_id:
            try:
                cookie_user_id_int = int(cookie_user_id)
            except ValueError:
                current_app.logger.warning("Invalid user_id cookie format.")
                return redirect(url_for("users.select_user"))
            
            api_base = current_app.config["BACKEND_API_URL"]
            try:
                success, user = get_user_from_backend(cookie_user_id_int)
                if success and user.get("id") == cookie_user_id_int:
                    session["user_id"] = cookie_user_id_int
                    session["username"] = user.get("username")  # Optional: populate this now to save work later
                    user_id_raw = cookie_user_id_int
                else:
                    return redirect(url_for("users.select_user"))
            except Exception as e:
                current_app.logger.error(f"Error validating user_id from cookie: {e}")
                return redirect(url_for("users.select_user"))
        else:
            return redirect(url_for("users.select_user"))

    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError):
        current_app.logger.warning("Invalid user_id in session.")
        return redirect(url_for("users.select_user"))

    username = session.get("username")
    if not username:
        success, user = get_user_from_backend(user_id)
        if success:
            username = user.get("username")
        else:
            return redirect(url_for("users.select_user"))  

    return render_template("rowing.html", user_id=user_id, username=username, ws_port=websocket_port)