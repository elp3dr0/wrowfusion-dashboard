## Readme
- [ ] make a note about configuring either:
* the router so that it has a local domain name, and then update the Caddyfile to use the hostname of the RPi plus the local domain name set in your router.
* or change the caddyfile so that the address is the IP address of the RPi, but then you'd have to navigate to that ip address in your browser, which isn't so elegant.
- [ ] Update the address in the Caddyfile during installation (can you find out the local domain name programatically?), should we set the hostname of the RPi or is that too overreaching for one application?
- [ ] Create config file that doesn't get overwritten. Especially for storing the local address for the caddy file. 

## CSS
- [ ] Change the fixed colours in components to variable names and set them in root of base.css.

## Routes
- [ ] Add something like the following to the routes that rely on the backend to handle failure cases:
import requests
from flask import render_template, flash

@app.route("/")
def index():
    try:
        response = requests.get("http://localhost:8000/api/users")
        response.raise_for_status()
        users = response.json()
    except requests.RequestException:
        flash("The backend is currently unavailable.", "error")
        users = []

    return render_template("select_user.html", users=users)


## Infrastructure
- [ ] Implement a conf file and use it to create a clean .env file during install. Be smart about updating values rather than overwriting .env
- [ ] During install, copy the working directory to temp and then at the end copy back the logs, database and .env. Then nuke the temp copy once everything else is successful. On error, roll back the installation and re-implement the temp working directory. Keep an installation log.
- [ ] Generate the secret key for the environment file during install.sh