import requests
from flask import (
    Blueprint, 
    redirect, 
    url_for, 
    flash,
    render_template,
    request, 
    session, 
    current_app, 
) 

users_bp = Blueprint("users", __name__)

@users_bp.route("/", methods=["GET"])
def root_redirect():
    try:
        api_base = current_app.config["BACKEND_API_URL"]
        response = requests.get(f"{api_base}/users")
        response.raise_for_status()
        users = response.json()
    except Exception as e:
        current_app.logger.error(f"Failed to fetch users: {e}")
        return "Error connecting to backend", 500

    saved_user_id = request.cookies.get("stay_logged_in_user_id")

    if saved_user_id and any(str(u["id"]) == saved_user_id for u in users):
        return redirect(url_for("rowing.show_rowing_page", user=saved_user_id))

    if len(users) == 1 and users[0]["id"] == 0:
        return redirect(url_for("rowing.show_rowing_page", user=0))

    return redirect(url_for("users.select_user"))

@users_bp.route("/select-user", methods=["GET", "POST"])
def select_user():
    
    api_base = current_app.config["BACKEND_API_URL"]

    if request.method == "POST":
        user_id = request.form.get("user_id")
        if not user_id:
            current_app.logger.warning("No user selected in select user form submission.")
            return render_template("select_user.html", users=[], error="No user selected.")
        stay_logged_in = request.form.get("stay_logged_in")

        # Validate against API
        resp = requests.post(f"{api_base}/validate_user", json={"user_id": user_id})
        if resp.status_code != 200 or not resp.json().get("valid"):
            current_app.logger.warning(f"User {user_id} could not be selected, because there is user with that id.")
            return render_template("select_user.html", users=[], error="Invalid user selected.")

        session["user_id"] = user_id
        response = redirect(url_for("rowing.show_rowing_page", user=user_id))

        if stay_logged_in:
            response.set_cookie("stay_logged_in_user_id", user_id, max_age=60*60*24*30)
        else:
            response.delete_cookie("stay_logged_in_user_id")

        current_app.logger.info(f"User {user_id} selected (stay_logged_in={bool(stay_logged_in)})")
        return response

    # Fetch users from API
    users_resp = requests.get(f"{api_base}/users")
    users = users_resp.json().get("users", []) if users_resp.ok else []

    if not users_resp.ok:
        current_app.logger.warning("Failed to fetch users from backend API.")
    
    return render_template("select_user.html", users=users)


@users_bp.route("/add_user", methods=["GET", "POST"])
def add_user_route():
    if request.method == "POST":
        username = request.form.get("username", "").strip()

        if not username:
            flash("User name is required.", "error")
            return redirect(url_for("users.add_user_route"))

        api_base = current_app.config["BACKEND_API_URL"]
        payload = {"username": username}

        try:
            resp = requests.post(f"{api_base}/users", json=payload)  # POST to /users per backend
            if resp.status_code == 409:
                flash("That user name is already taken.", "error")
                current_app.logger.warning(f"Add user failed - username already exists: '{username}'")
                return redirect(url_for("users.add_user_route"))

            resp.raise_for_status()
            user_id = resp.json().get("id") or resp.json().get("user_id")

            if not user_id:
                raise ValueError("User ID not returned from backend")

        except requests.RequestException as e:
            current_app.logger.exception(f"API error when adding user '{username}': {e}")
            flash("An error occurred while adding the user. Please try again later.", "error")
            return redirect(url_for("users.add_user_route"))

        session["user_id"] = user_id
        current_app.logger.info(f"New user added via API and logged in: {username} (ID: {user_id})")
        flash(f"Welcome, {username}!", "success")
        return redirect(url_for("rowing.show_rowing_page"))

    return render_template("add_user.html")
