import time
from functools import wraps
from flask import request, jsonify
import threading

class RateLimiter:
    def __init__(self):
        self.requests = {}
        self.lock = threading.Lock()

    def is_allowed(self, key, limit, period):
        now = time.time()
        cutoff = now - period
        with self.lock:
            # Clean up old entries
            if key not in self.requests:
                self.requests[key] = []
            
            # Filter requests in the current window
            self.requests[key] = [t for t in self.requests[key] if t > cutoff]
            
            if len(self.requests[key]) < limit:
                self.requests[key].append(now)
                return True
            return False

limiter = RateLimiter()

def rate_limit(limit=60, period=60):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            ip = request.headers.get('X-Forwarded-For', request.remote_addr) or 'unknown'
            key = f"{f.__name__}:{ip}"
            
            if not limiter.is_allowed(key, limit, period):
                return jsonify({
                    "error": "Too many requests. Please try again later.",
                    "status": 429
                }), 429
            return f(*args, **kwargs)
        return wrapped
    return decorator
