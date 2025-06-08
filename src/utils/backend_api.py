import requests
from flask import current_app
from typing import Any

def get_users_from_backend() -> tuple[bool, list[dict[str, Any]]]:
    """Fetch users from the backend API.

    Returns a tuple (success, users_list). If success is False, users_list will be empty.
    """
    api_base = current_app.config.get("BACKEND_API_URL")
    if not api_base:
        current_app.logger.error("BACKEND_API_URL not configured.")
        return False, []

    try:
        resp = requests.get(f"{api_base}/users")
        resp.raise_for_status()
        data = resp.json()

        users = data.get("users")
        if not isinstance(users, list):
            current_app.logger.error("Malformed response: 'users' is not a list.")
            return False, []

        return True, users

    except requests.RequestException as e:
        current_app.logger.error(f"Error fetching users from backend: {e}")
    except ValueError as e:
        current_app.logger.error(f"Error parsing JSON from backend: {e}")

    return False, []

def get_user_from_backend(user_id: int) -> tuple[bool, dict[str, Any]]:
    api_base = current_app.config["BACKEND_API_URL"]
    if not api_base:
        current_app.logger.error("BACKEND_API_URL not configured.")
        return False, {}

    try:
        resp = requests.get(f"{api_base}/users/{user_id}")
        resp.raise_for_status()
        data = resp.json()

        user = data.get("user")
        if not isinstance(user, dict):
            current_app.logger.error(f"Malformed response: 'user' is not a dict. Got: {type(user)}")
            return False, {}
        
        return True, user
    
    except requests.RequestException as e:
        current_app.logger.error(f"Error fetching user {user_id} from backend: {e}")
    except ValueError as e:
        current_app.logger.error(f"Error parsing JSON for user {user_id}: {e}")

    return False, {}