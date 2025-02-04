from pathlib import Path
from smtplib import SMTP
from abc import ABC, abstractmethod

class FileOpen:
    def __init__(self, file_path: Path, operation: str):
        self.file_path = file_path
        self.operation = operation
        self._file = None

    def __enter__(self):
        if "b" in self.operation:
            self._file = open(self.file_path, self.operation)
        else:
            self._file = open(self.file_path, self.operation, encoding="utf-8")
        return self._file
    
    def __exit__(self, _, __, ___):
        if self._file:
            self._file.close()

class SmtpOpen:
    def __init__(self, smtp_server: str, smtp_port: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self._smtp = None

    def __enter__(self):
        self._smtp = SMTP(self.smtp_server, self.smtp_port)
        return self._smtp
    
    def __exit__(self, _, __, ___):
        self._smtp.close()

