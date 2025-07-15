import os
import multiprocessing

# Server socket - Railway provides PORT environment variable
port = os.environ.get("PORT", "5000")
bind = f"0.0.0.0:{port}"
backlog = 2048

# Worker processes - optimized for cloud deployment
workers = 2  # Fixed number for better stability on Railway
worker_class = "sync"
worker_connections = 1000
timeout = 300  # Increased for video downloads
keepalive = 5

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "video_downloader"

# Server mechanics
daemon = False
preload_app = True  # Important for Railway
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
