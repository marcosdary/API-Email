from app.config import Config
from json import dump, load
from app.utils import FileOpen
from dropbox import Dropbox, files, exceptions, dropbox_client

class Json:
    path_log = Config.PATH_LOGGING.value

    def to_clean(self):
        json_file_writer = FileOpen(
            file_path=self.path_log,
            operation="w"
        )
        with json_file_writer as file:
            dump([], file, ensure_ascii=False)

    def to_write(self, history_log: dict):
        json_file_writer = FileOpen(
            file_path=self.path_log,
            operation="w"
        )
        email_communication_log = self.to_read()
        body = {
            "name": history_log["name"],
            "datetime": history_log["datetime"],
            "message": history_log["message"]
        }
        for email in email_communication_log:
            if email["email"] == history_log["email"]:
                email["history"].append(body)
                break
        else:
            new_log = {
                "email": history_log["email"],
                "history": [body]
            }
            email_communication_log.append(new_log)
        with json_file_writer as file:
            dump(email_communication_log, file, indent=4, ensure_ascii=False)
        return True
    
    def to_write_nuvem(self, history_log: list):
        json_file_writer = FileOpen(
            file_path=self.path_log,
            operation="w"
        )
        with json_file_writer as file:
            dump(history_log, file, indent=4, ensure_ascii=False)
        return True

    def to_read(self):
        json_file_reader = FileOpen(
            file_path=self.path_log, 
            operation="r"
        )
        with json_file_reader as file:
            return load(file)
        

class DropboxAccess:
    def __init__(self):
        self._access_key = ""

    @property
    def access_key(self):
        return self._access_key
    
    @access_key.setter
    def access_key(self, key: str):
        self._access_key = key

    def connect_to_dropbox(self):
        try:
            dbx = Dropbox(self.access_key)
            user_info = dbx.users_get_current_account()
            return {"dbx": dbx}
        except exceptions.AuthError:
            return {
                "dbx": None, 
                "error": "Erro de autenticação - A chave de acesso fornecida é inválida ou expirou.", 
                "message": "Não foi possível conectar ao Dropbox. Verifique sua chave de acesso e tente novamente."
            }
        except dropbox_client.BadInputException as e:
            return {
                "dbx": None, 
                "error": f"Erro ao enviar o token de acesso ao Dropbox: {e}",
                "message": "Não foi possível conectar ao Dropbox. Verifique a entrada e tente novamente."
            }
        except Exception as e:
            return {
                "dbx": None, 
                "error": f"Erro inesperado ao conectar ao Dropbox: {e}", 
                "message": "Houve um erro ao tentar conectar ao Dropbox. Tente novamente mais tarde."
            } 
        
class DropboxOperation:
    def __init__(self, dbx: Dropbox = ""):
        self.dbx = dbx
        self.local_file_path = Config.PATH_LOGGING.value
        self.dropbox_path = Config.PATH_LOGGING_NUVEM.value

    def upload(self):
        try:
            with FileOpen(self.local_file_path, "rb") as file:
                # Faz o upload do arquivo para o Dropbox
                self.dbx.files_upload(file.read(), self.dropbox_path, mode=files.WriteMode("overwrite"))
            return {"status": True}
        except Exception as e:
            return {
                "status": False, 
                "error": f"Erro ao realizar o upload do arquivo {self.local_file_path}: {e}", 
                "message": "Ocorreu um erro ao fazer o upload. Tente novamente mais tarde."
            }

    def download(self):
        try:
            metadata, response = self.dbx.files_download(self.dropbox_path)
            with FileOpen(self.local_file_path, "wb") as file:
                file.write(response.content)
            return {"status": True}
        
        except exceptions.ApiError as e:
            if e.error.is_path() and e.error.get_path().is_not_found():
                return {
                    "status": False, 
                    "error": "Caminho não encontrado no Dropbox. O arquivo pode ter sido removido.",
                    "message": "Não foi possível encontrar o arquivo no Dropbox. Verifique se ele está disponível."
                }
            
            return {
                "status": False, 
                "error": f"Erro desconhecido ao tentar fazer o download do arquivo: {e}",
                "message": "Ocorreu um erro ao tentar baixar o arquivo. Tente novamente mais tarde."
            }
        
        except Exception as e:
            return {
                "status": False, 
                "error": f"Erro desconhecido ao realizar o download: {e}",
                "message": "Não foi possível baixar o arquivo. Tente novamente mais tarde."
            }
        
    def delete(self):
        try:
            self.dbx.files_delete_v2(self.dropbox_path)
            return {"status": True}
        except exceptions.ApiError as e:
            return {
                "status": False, 
                "error": f"Erro na API do Dropbox ao tentar excluir o arquivo: {e}",
                "message": "Houve um problema ao tentar excluir o arquivo. Tente novamente mais tarde."
            }
        except Exception as e:
            return {
                "status": False, 
                "error": f"Erro desconhecido ao excluir o arquivo: {e}",
                "message": "Não foi possível excluir o arquivo. Tente novamente mais tarde."
            }
