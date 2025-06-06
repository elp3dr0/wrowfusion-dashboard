import requests
from flask import current_app

def get_users_from_backend() -> tuple[bool, list[dict]]:
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
