"""
Configuración de Gunicorn para producción en Render
"""
import os

# Bind
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# Workers
workers = int(os.environ.get('WEB_CONCURRENCY', 2))
worker_class = 'sync'

# Timeouts
timeout = 120
graceful_timeout = 120
keepalive = 5

# Memory limits
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Preload
preload_app = False

# Worker temp directory
worker_tmp_dir = '/dev/shm'

print(f"✓ Gunicorn configurado: {workers} workers, timeout {timeout}s")
