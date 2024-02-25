"""Gunicorn *production* config file"""

# Django WSGI application path in pattern MODULE_NAME:VARIABLE_NAME
wsgi_app = "app:app"
# The granularity of Error log outputs
loglevel = "debug"
# The number of worker processes for handling requests
workers = 4
# The socket to bind
bind = "0.0.0.0:5000"
# Restart workers when code changes (development only!)
reload = False
# Write access and error info to /var/log
accesslog = errorlog = "/var/log/gunicorn/oauth_prod.log"
# Redirect stdout/stderr to log file
capture_output = True
# PID file so you can easily fetch process ID
pidfile = "/var/run/gunicorn/oauth_prod.pid"
# Daemonize the Gunicorn process (detach & enter background)
daemon = False
