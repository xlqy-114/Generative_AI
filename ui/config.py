import os
import json
import hashlib
import base64

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

class Config:
    SALT = b'financial-auto-analysis-salt'

    def __init__(self):
        # Default download directory
        self.default_download_dir = os.getcwd()
        # Assistant ID
        self.assistant_id = ""
        # API Key
        self.api_key = ""
        # Saved API Keys
        self.saved_api_keys = {}
        self.config_path = os.path.join(
            os.path.dirname(__file__),
            ".financial_auto_analysis_config.json"
        )
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.default_download_dir = data.get(
                    "default_download_dir", self.default_download_dir
                )
                self.assistant_id = data.get("assistant_id", self.assistant_id)
                self.saved_api_keys = data.get("saved_api_keys", {})
        except Exception:
            pass

    def save(self):
        """Write config to file."""
        data = {
            "default_download_dir": self.default_download_dir,
            "assistant_id": self.assistant_id,
            "saved_api_keys": self.saved_api_keys
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _derive_key(self, pin: str) -> bytes:
        if not CRYPTO_AVAILABLE:
            return None
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.SALT,
            iterations=390000,
        )
        return base64.urlsafe_b64encode(kdf.derive(pin.encode()))

    def encrypt_api_key(self, api_key: str, pin: str) -> str:
        if CRYPTO_AVAILABLE:
            f = Fernet(self._derive_key(pin))
            return f.encrypt(api_key.encode()).decode()
        else:
            return base64.b64encode(api_key.encode()).decode()

    def decrypt_api_key(self, token: str, pin: str) -> str:
        if CRYPTO_AVAILABLE:
            f = Fernet(self._derive_key(pin))
            return f.decrypt(token.encode()).decode()
        else:
            return base64.b64decode(token.encode()).decode()

config = Config()
