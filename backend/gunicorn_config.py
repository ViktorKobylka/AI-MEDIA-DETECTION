# gunicorn_config.py
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"

# Worker processes
workers = 2
worker_class = "sync"

# Timeouts
timeout = 120
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "deepfake_detector"

# Server mechanics
daemon = False
pidfile = None

# Reload
reload = False

# Max requests (prevent memory leaks)
max_requests = 1000
max_requests_jitter = 50