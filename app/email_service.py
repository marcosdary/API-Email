from app.config import Config
from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.utils import FileOpen, SmtpOpen
from datetime import datetime

class EmailSend:

    def __init__(self, name: str, email: str, message: str, subject: str):
        self.name = name
        self.email = email
        self.message = message
        self.subject = subject
        self.datetime_current = datetime.now()
        self.__template = {
            "name": self.name,
            "email": self.email,
            "message": self.message,
            "subject": self.subject,
            "datetime": self.datetime_current.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.__config = Config

    def send(self):
        with FileOpen(self.__config.HTML_FILE_PATH.value, "r") as file:
            TEMPLATE = Template(file.read())
            EMAIL = TEMPLATE.substitute(self.__template)

        mime_multipart = MIMEMultipart()
        mime_multipart["from"] = self.__config.SENDER.value
        mime_multipart["to"] = self.email
        mime_multipart["subject"] = self.subject

        email_body = MIMEText(EMAIL, "html", "utf-8")
        mime_multipart.attach(email_body)

        with SmtpOpen(self.__config.SMTP_SERVER.value, self.__config.SMTP_PORT.value) as server:
            server.ehlo()
            server.starttls()
            server.login(self.__config.SMTP_USERNAME.value, self.__config.SMTP_PASSWORD.value)

            try:
                server.send_message(mime_multipart)
                return {"status": True, "message": "E-mail enviado com sucesso"}
            except Exception as e:
                return {"status": False, "message": f"Falha ao enviar e-mail: {e}"}
    
    @property
    def history_log(self):
        return {
            "email": self.email,
            "name": self.name,
            "datetime": self.datetime_current.strftime("%Y-%m-%d %H:%M:%S"),
            "message": self.message
        }



