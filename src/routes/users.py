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
from src.utils.backend_api import get_users_from_backend, get_user_from_backend

users_bp = Blueprint("users", __name__)

class LoginError(Exception):
    pass

def login_user(user_id: int) -> str:
    """
    Attempts to log in the user with the given ID by calling the backend auth/login endpoint.
    On success, sets user_id and username in Flask session.
    Raises LoginError on failure.
    Returns the username on success
    """
    api_base = current_app.config["BACKEND_API_URL"]

    try:
        login_api_resp = requests.post(f"{api_base}/auth/login/", json={"id": user_id})
        login_api_resp.raise_for_status()
        login_data = login_api_resp.json()
    except Exception as e:
        raise LoginError(f"Backend error: {e}")

    if not login_data.get("success", False):
        raise LoginError("Invalid user id")

    # Successful login: set session and cookie
    user = login_data.get("user", {})
    username = user.get("username")
    if username:
        session["username"] = username
    session["user_id"] = user_id

    current_app.logger.info(f"User {user_id}-{username} logged in.")

    return username

@users_bp.route("/", methods=["GET"])
def root_redirect() -> ResponseReturnValue:
    saved_user_id = request.cookies.get("stay_logged_in_user_id")

    if saved_user_id:
        try:
            user_id = int(saved_user_id)
            # Attempt to login using helper function
            login_user(user_id)
            current_app.logger.info(f"Auto-login successful for user {user_id} via cookie.")
            return redirect(url_for("rowing.show_rowing_page"))
        except (ValueError, LoginError) as e:
            current_app.logger.warning(f"Auto-login failed for user_id '{saved_user_id}': {e}")

    # If no valid cookie or login failed, fetch all users
    success, users = get_users_from_backend()
    if not success:
        current_app.logger.error("Error connecting to backend")
        return "Error connecting to backend", 500

    # If only one user and user id is 0, login as that user automatically
    if len(users) == 1 and users[0].get("id") == 0:
        try:
            login_user(0)
            current_app.logger.info("Auto-login as guest user (id=0)")
            return redirect(url_for("rowing.show_rowing_page"))
        except LoginError as e:
            current_app.logger.error(f"Failed to auto-login guest user: {e}")
            return "Error connecting to backend", 500

    # Otherwise, redirect to user selection page
    return redirect(url_for("users.select_user"))

@users_bp.route("/select-user", methods=["GET", "POST"])
def select_user() -> ResponseReturnValue:
    
    api_base = current_app.config["BACKEND_API_URL"]

    if request.method == "POST":
        user_id_str  = request.form.get("user_id")
        if not user_id_str :
            current_app.logger.warning("No user selected in select user form submission.")
            success, users = get_users_from_backend()
            if not success:
                current_app.logger.warning("Failed to fetch users from backend API.")
                users = []
            return render_template("select_user.html", users=users, error="No user selected.")
        
        stay_logged_in = request.form.get("stay_logged_in")

        try:
            user_id = int(user_id_str)
        except ValueError:
            current_app.logger.warning(f"Invalid user_id format: {user_id_str}")
            success, users = get_users_from_backend()
            if not success:
                current_app.logger.warning("Failed to fetch users from backend API.")
                users = []
            return render_template("select_user.html", users=users, error="Invalid user selected.")

        # Use the helper function to handle login and session setup
        try:
            login_user(user_id)
        except LoginError as e:
            current_app.logger.warning(f"Login failed for user {user_id}: {e}")
            success, users = get_users_from_backend()
            if not success:
                current_app.logger.warning("Failed to fetch users from backend API.")
                users = []
            return render_template("select_user.html", users=users, error=str(e))
        
        flask_resp = redirect(url_for("rowing.show_rowing_page"))

        if stay_logged_in:
            flask_resp.set_cookie("stay_logged_in_user_id", str(user_id), max_age=60*60*24*60)
        else:
            flask_resp.delete_cookie("stay_logged_in_user_id")

        current_app.logger.info(f"User {user_id} logged in (stay_logged_in={bool(stay_logged_in)})")
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
            
            user_dict = users_json.get("user", {})
            user_id = user_dict.get("id")
            if not user_id:
                raise ValueError("User ID not returned from backend")

        except requests.RequestException as e:
            current_app.logger.exception(f"API error when adding user '{username}': {e}")
            flash("An error occurred while adding the user. Please try again later.", "error")
            return redirect(url_for("users.add_user_route"))


        # Use the helper function to handle login and session setup
        try:
            login_user(user_id)
        except LoginError as e:
            current_app.logger.warning(f"Login failed for user {user_id}: {e}")
            success, users = get_users_from_backend()
            if not success:
                current_app.logger.warning("Failed to fetch users from backend API.")
                users = []
            return render_template("select_user.html", users=users, error=str(e))
        
        flask_resp = redirect(url_for("rowing.show_rowing_page"))

        if stay_logged_in:
            flask_resp.set_cookie("stay_logged_in_user_id", str(user_id), max_age=60*60*24*60)
        else:
            flask_resp.delete_cookie("stay_logged_in_user_id")

        current_app.logger.info(f"User {user_id} logged in (stay_logged_in={bool(stay_logged_in)})")
        flash(f"Welcome, {username}!", "success")
        return flask_resp
    
    return render_template("add_user.html")
