## Readme
- [ ] make a note about configuring either:
* the router so that it has a local domain name, and then update the Caddyfile to use the hostname of the RPi plus the local domain name set in your router.
* or change the caddyfile so that the address is the IP address of the RPi, but then you'd have to navigate to that ip address in your browser, which isn't so elegant.
- [ ] Update the address in the Caddyfile during installation (can you find out the local domain name programatically?), should we set the hostname of the RPi or is that too overreaching for one application?
- [ ] Create config file that doesn't get overwritten. Especially for storing the local address for the caddy file. 
