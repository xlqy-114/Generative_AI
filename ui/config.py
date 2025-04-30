import os

class Config:
    def __init__(self):
        # Default directory for downloads
        self.default_download_dir = os.getcwd()
        # Assistant ID to be set by the user in Settings
        self.assistant_id = ""

config = Config()
