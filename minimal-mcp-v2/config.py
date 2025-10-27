# config.py
import os
from typing import Optional

class Settings:
    RANCHER_URL: str
    RANCHER_TOKEN: str
    RANCHER_CA_BUNDLE: Optional[str]
    HTTP_TIMEOUT: float
    MAX_RETRIES: int

    def __init__(self) -> None:
        self.RANCHER_URL = os.environ.get("RANCHER_URL", "").rstrip("/")
        self.RANCHER_TOKEN = os.environ.get("RANCHER_TOKEN", "")
        self.RANCHER_CA_BUNDLE = os.environ.get("RANCHER_CA_BUNDLE")  # path to CA file, optional
        self.HTTP_TIMEOUT = float(os.environ.get("HTTP_TIMEOUT", "15"))
        self.MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))

        if not self.RANCHER_URL or not self.RANCHER_TOKEN:
            raise RuntimeError("RANCHER_URL and RANCHER_TOKEN must be set")

settings = Settings()
