import requests
from flask import (
    Blueprint, 
    Response,
    redirect, 
    url_for, 
    flash,
    render_template,
    request, 
    session, 
    current_app,
) 
from flask.typing import ResponseReturnValue
from src.utils.backend_api import get_users_from_backend

users_bp = Blueprint("users", __name__)

@users_bp.route("/", methods=["GET"])
def root_redirect() -> ResponseReturnValue:
    success, users = get_users_from_backend()

    if not success:
        return "Error connecting to backend", 500

    saved_user_id = request.cookies.get("stay_logged_in_user_id")

    if saved_user_id and any(str(u.get("id")) == saved_user_id for u in users):
        return redirect(url_for("rowing.show_rowing_page", user=saved_user_id))

    if len(users) == 1 and users[0].get("id") == 0:
        return redirect(url_for("rowing.show_rowing_page", user=0))

    return redirect(url_for("users.select_user"))

@users_bp.route("/select-user", methods=["GET", "POST"])
def select_user() -> ResponseReturnValue:
    
    api_base = current_app.config["BACKEND_API_URL"]

    if request.method == "POST":
        user_id = request.form.get("user_id")
        if not user_id:
            current_app.logger.warning("No user selected in select user form submission.")
            success, users = get_users_from_backend()
            if not success:
                current_app.logger.warning("Failed to fetch users from backend API.")
                users = []
            return render_template("select_user.html", users=users, error="No user selected.")
        stay_logged_in = request.form.get("stay_logged_in")

        # Validate against API
        try:
            validation_api_resp = requests.post(f"{api_base}/validate", json={"user_id": user_id})
            validation_api_resp.raise_for_status()
            valid = validation_api_resp.json().get("valid", False)
        except Exception as e:
            current_app.logger.warning(f"Failed to validate user {user_id}: {e}")
            success, users = get_users_from_backend()
            if not success:
                current_app.logger.warning("Failed to fetch users from backend API.")
                users = []
            return render_template("select_user.html", users=users, error="Error validating user.")
        
        if not valid:
            current_app.logger.warning(f"User {user_id} could not be selected; invalid user id.")
            success, users = get_users_from_backend()
            if not success:
                current_app.logger.warning("Failed to fetch users from backend API.")
                users = []
            return render_template("select_user.html", users=users, error="Invalid user selected.")

        session["user_id"] = user_id
        flask_resp = redirect(url_for("rowing.show_rowing_page", user=user_id))

        if stay_logged_in:
            flask_resp.set_cookie("stay_logged_in_user_id", user_id, max_age=60*60*24*60)
        else:
            flask_resp.delete_cookie("stay_logged_in_user_id")

        current_app.logger.info(f"User {user_id} selected (stay_logged_in={bool(stay_logged_in)})")
        return flask_resp

    # Handle GET: Fetch users from API
    success, users = get_users_from_backend()
    if not success:
        current_app.logger.warning(f"Failed to fetch users from backend API")
        users = []

    return render_template("select_user.html", users=users)


@users_bp.route("/add_user", methods=["GET", "POST"])
def add_user_route():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        stay_logged_in = request.form.get("stay_logged_in")

        if not username:
            flash("User name is required.", "error")
            return redirect(url_for("users.add_user_route"))

        api_base = current_app.config["BACKEND_API_URL"]
        payload = {"username": username}

        try:
            users_api_resp = requests.post(f"{api_base}/users/", json=payload)
            if users_api_resp.status_code == 409:
                flash("That user name is already taken.", "error")
                current_app.logger.warning(f"Add user failed - username already exists: '{username}'")
                return redirect(url_for("users.add_user_route"))

            users_api_resp.raise_for_status()
            try:
                users_json = users_api_resp.json()
            except ValueError:
                current_app.logger.error(f"Backend returned non-JSON response: {users_api_resp.text}")
                raise ValueError("Backend returned invalid JSON")
            
            if not isinstance(users_json, dict):
                raise ValueError("Unexpected response format from backend.")
            
            user_id = users_json.get("id")
            if not user_id:
                raise ValueError("User ID not returned from backend")

        except requests.RequestException as e:
            current_app.logger.exception(f"API error when adding user '{username}': {e}")
            flash("An error occurred while adding the user. Please try again later.", "error")
            return redirect(url_for("users.add_user_route"))

        session["user_id"] = user_id
        flask_resp = redirect(url_for("rowing.show_rowing_page", user=user_id))

        if stay_logged_in:
            flask_resp.set_cookie("stay_logged_in_user_id", user_id, max_age=60*60*24*60)
        else:
            flask_resp.delete_cookie("stay_logged_in_user_id")

        current_app.logger.info(f"New user added via API and logged in: {username} (ID: {user_id})")
        flash(f"Welcome, {username}!", "success")
        return flask_resp

    return render_template("add_user.html")
