from flask import request, Flask, jsonify
from app.email_service import EmailSend, Config
from app.logger_service import Json, DropboxAccess, DropboxOperation
from functools import wraps

app = Flask(__name__)

config = Config

USERNAME = config.USERNAME.value
PASSWORD = config.PASSWORD.value

dropbox_access = DropboxAccess()
dropbox_operation = DropboxOperation()
json = Json()

def ensure_dropbox_connection(func):

    @wraps(func)
    def wrapper_ensure_connection(*args, **kwds):
        connection = dropbox_access.connect_to_dropbox()
        if (connection["dbx"] is None): 
            return jsonify({
                "status": False,
                "error": connection["error"],
                "message": connection["message"]
            }), 503 
        """
        Se a conexão falhar 'connection["dbx"] is None' a função retorna uma resposta JSON com um status de erro e um código HTTP 503 (Serviço Indisponível).
        Função wraps() manter os metadados da função que é decorada.
        """
        return func(*args, **kwds)
    
    return wrapper_ensure_connection

def cloud_storage(func):

    @wraps(func) 
    def wrapper_cloud_storage(*args, **kwds):
        auth = request.authorization
        if not auth or auth.username != USERNAME or auth.password != PASSWORD:
            return jsonify({
                "error": "Autenticação Necessária",
                "message": "Por favor, forneça as credenciais corretas para acessar este recursos."
            }), 401, {
                "WWW-Authenticate": 'Basic realm="Login Necessário"'
            }
        """
        Se as credenciais não forem válidas, retorna uma resposta JSON com uma mensagem de erro e o código
        de status HTTP 401 (Não Autorizado), além de uma cabeçalho WWW-Authenticate para indicar que a autenticação
        é necessária.
        """
        return func(*args, **kwds)
    
    return wrapper_cloud_storage

@app.route("/user/email/send", methods=["POST"])
@ensure_dropbox_connection
def user_email_send():
    user_data = request.get_json()
    if len(user_data) != 4:
        return jsonify({
            "status": False,
            "error": "Os campos (E-mail, Nome, Mensagem, Assunto) são obrigatórios."
        })
    """
    Campos da dados enviado ao servidor:
    """
    email = user_data["email"]
    name = user_data["name"]
    subject = user_data["subject"]
    message = user_data["message"]
    
    email_send = EmailSend(
        name=name, email=email, message=message, subject=subject
    )
    return_email_send = email_send.send()
    if return_email_send["status"]:
        connection = dropbox_access.connect_to_dropbox()
        dropbox_operation.dbx = connection["dbx"]
        dropbox_operation.download()
        json.to_write(email_send.history_log)
        operation_return = dropbox_operation.upload()
        json.to_clean()

        if not operation_return["status"]:
            return jsonify(operation_return)
        return jsonify(return_email_send)
    
    return jsonify(return_email_send)

"""
Explicação da rota /user/email/send
Primeiramente recebe os dados que foram enviados para servidor; depois são analisados que estão com a quantidade permi-
tido caso não estiver é enviado uma retorno em json, com base no enviado.
Segundamente é estabelecido a conexão com o servidor para realizar as operações de envio de email. Caso todas as opera-
ções sejam retornadas com status True, começa o processo de realizar o processo de upload da nuvem para o local, para 
atualizar juntamente com o novo histórico que serão armazenado.
Depois será salvo o histórico na pasta /logs/log.json e enviado para a nuvem, por fim ele é limpo com a função 
json.to_clean(). 
Mas esta operação só ocorre se o email retorna o status = True.
"""   

@app.route("/admin/dropbox/update-token", methods=["POST"])
@cloud_storage
def admin_dropbox_updateToken():
    admin_data = request.get_json()
    if admin_data == {}:
        return jsonify({
            "status": False,
            "error": "Token de acesso inválido ou ausente. Por favor, forneça um token válido."
        }), 400
    key = admin_data["key"]
    dropbox_access.access_key = key
    connection = dropbox_access.connect_to_dropbox()

    if connection["dbx"] is None:
        return jsonify({
            "status": False,
            "error": "Token de acesso expirou, por favor forneça outro.",
        })
    return jsonify({
        "status": True,
        "message": "Token de acesso atualizado com sucesso!"
    })
"""
Verifica se os dados recebidos estão vazios. Se estiverem, retorna uma resposta JSON com um erro e status HTTP 
400 (Bad Request).
"""

@app.route("/admin/dropbox/email-log", methods=["GET"])
@ensure_dropbox_connection
@cloud_storage
def admin_dropbox_emailLog():
    connection = dropbox_access.connect_to_dropbox()
    dropbox_operation.dbx = connection["dbx"]
    return_operation = dropbox_operation.download()
    
    if not return_operation["status"]:
        return jsonify(return_operation)
    
    users = json.to_read()
    json.to_clean()

    return jsonify({
        "status": True,
        "message": "Histórico de e-mails recuperado com sucesso.",
        "data": users
    })
"""
Realizar a operação de enviados os históricos de e-mails para o admin, para que sejam realizados uma determinada
atividade. Primeiramente, o download é analisado para que caso o status sejam False, ele retorna o erro para o 
admin, para que seja analisado e consultado. Se não ocorrer, ocorre a leitura para uma variável 'users', depois 
limpeza e o envio em formato JSON. 
"""

@app.errorhandler(404)
def route_not_found():
    return jsonify({
        "status": False,
        "error": "Rota não encontrada. Verifique a URL solicitada."
    }), 404
"""
404: NOT FOUND 
"""

@app.route("/", methods=["GET"])
def get_info():
    info = {
        "version": "1.0",
        "description": "API que lida com o envio de e-mails e armazenamento de arquivos no Dropbox.",
        "routes": {
            "/user/email/send": "Envia um e-mail com os dados fornecidos e salva no Dropbox.",
            "/help": "Fornece informações sobre as rotas disponíveis e como usá-las.",
            "/admin": "Acesso ao painel administrativo para gerenciar a integração com o Dropbox.",
            "/admin/dropbox/update-token": "Atualiza o token de acesso ao Dropbox.",
            "/admin/dropbox/email-log": "Recupera o histórico de e-mails armazenados no Dropbox."
        }
    }
    return jsonify(info)


@app.route("/help", methods=["GET"])
def get_help():
    help_info = {
        "/user/email/send": {
            "description": "Envia um e-mail e salva os dados do usuário no Dropbox.",
            "method": "POST",
            "request_body": {
                "name": "Nome do usuário",
                "email": "E-mail do usuário",
                "subject": "Assunto do e-mail",
                "message": "Mensagem do e-mail"
            },
            "response": {
                "status": "Status da operação",
                "message": "Mensagem de sucesso ou erro"
            }
        },
        "/api/help": {
            "description": "Retorna informações de ajuda sobre a API.",
            "method": "GET",
            "response": {
                "post_email": "Exemplo de dados para enviar um e-mail",
                "detalhes": "Descrição das rotas e métodos disponíveis na API"
            }
        },
        "/admin/dropbox/update-token": {
            "description": "Atualiza o token de acesso ao Dropbox.",
            "method": "POST",
            "request_body": {
                "key": "Novo token de acesso ao Dropbox"
            },
            "response": {
                "status": "Status da operação",
                "message": "Mensagem indicando o sucesso ou erro"
            }
        },
        "/admin/dropbox/email-log": {
            "description": "Recupera o histórico de e-mails armazenados no Dropbox.",
            "method": "GET",
            "response": {
                "status": "Status da operação",
                "message": "Mensagem de sucesso ou erro",
                "data": "Lista dos e-mails armazenados"
            }
        }
    }

    return jsonify(help_info)

"""
O decorator @app.route é usado no Flask, um microframework para Python, para associar uma URL específica a uma função
de visualização. Isso significa que quando um cliente faz uma requisição HTTP para essa URL, a função associada será 
chamada para processar a requisição e retornar uma resposta.

Os métodos HTTP suportados pelo Flask no decorator @app.route incluem:
GET: Recupera dados do servidor.
POST: Envia dados ao servidor para criar ou atualizar um recurso.
PUT: Atualiza um recurso existente no servidor.
DELETE: Remove um recurso do servidor.
PATCH: Aplica modificações parciais a um recurso.
OPTIONS: Descreve as opções de comunicação para o recurso alvo.
HEAD: Recupera os cabeçalhos de resposta, sem o corpo da resposta
"""

if __name__ == "__main__":
    app.run(debug=True)