# gunicorn_config.py

# Number of worker processes (recommended: 2 * number of CPU cores + 1)
workers = 3

# Bind address (use 0.0.0.0:8000 to bind to all IP addresses on port 8000)
bind = '0.0.0.0:8000'

# Logging level 
# loglevel = 'info'
loglevel = 'debug'

# Enable access log
accesslog = '-'

# Enable error log
errorlog = '-'

timeout = 300  # or any value suitable for your use case
