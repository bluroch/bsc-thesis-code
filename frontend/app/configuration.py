"""
This module stores the configuration for the application.
"""

from os import environ

class Config():
    """
    Configuration class for the frontend application.
    """

    def __init__(self):
        self.admin_email = environ.get("DEFAULT_ADMIN_EMAIL") or "admin@gagm.com"
        self.admin_pass = environ.get("DEFAULT_ADMIN_PASS") or "pass"
        self.backend_ip = environ.get("BACKEND_IP") or "127.0.0.1"
        self.backend_port = environ.get("BACKEND_PORT") or 8000
        self.backend_secret = environ.get("BACKEND_KEY")
        self.debug_mode = environ.get("DEBUG_MODE") or False
        self.ssl_enabled = environ.get("SSL_ENABLED") or False

    def backend_url(self):
        url: str = "https://" if self.ssl_enabled else "http://"
        url += f"{self.backend_ip}:{self.backend_port}"
        return url


CONFIG: Config = Config()