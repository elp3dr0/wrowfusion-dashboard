from flask import Blueprint, request, redirect, url_for, render_template, session, current_app
import requests
import os

rowing_bp = Blueprint("rowing", __name__)

@rowing_bp.route("/rowing")
def show_rowing_page():
    user_id = session.get("user_id")
    websocket_port = os.environ.get("WRFD_WROWFUSION_WEBSOCKET_PORT", 8765)
    if not user_id:
        cookie_user_id = request.cookies.get("stay_logged_in_user_id")
        if cookie_user_id:
            # Optional: Validate user_id with backend API before trusting it
            api_base = current_app.config["BACKEND_API_URL"]
            try:
                resp = requests.get(f"{api_base}/users/{cookie_user_id}")
                if resp.ok and resp.json().get("id") == int(cookie_user_id):
                    session["user_id"] = cookie_user_id
                    user_id = cookie_user_id
                else:
                    return redirect(url_for("users.select_user"))
            except Exception as e:
                current_app.logger.error(f"Error validating user_id from cookie: {e}")
                return redirect(url_for("users.select_user"))
        else:
            return redirect(url_for("users.select_user"))

    return render_template("rowing.html", user_id=user_id, ws_port=websocket_port)