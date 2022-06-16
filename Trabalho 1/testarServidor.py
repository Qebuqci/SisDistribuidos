#-*- encoding: utf-8 -*-

''' Script em python com módulos de teste para o Servidor Central
do Chat Distribuído '''

import socket, json

# Teste que realiza uma requisição de login corretamente (como foi especificado no documento do trabalho) #
def teste_ReqLogin1(HOSTSC, PORTSC, socket):
    requisicao_servidor = {
        "operacao": "login",
        "username": "USUARIO TESTE",
        "porta": 25641
    }
    requisicaoJSON = json.dumps(requisicao_servidor)
    # Prepara o envio da requisição
    tamRequisicao = len(requisicaoJSON)
    tamReqBytes = tamRequisicao.to_bytes(2, "big")
    socket.sendall(tamReqBytes)
    bytesEnviados = bytes(requisicaoJSON, "utf-8")
    socket.sendall(bytesEnviados)
    
    # Prepara a recepção da resposta
    first2Bytes = socket.recv(2)
    tamResposta = int.from_bytes(first2Bytes, "big")
    bytesRecebidos = socket.recv(tamResposta + 1024)    # Recebe como resposta o tamResposta + 1KB de auxílio
    
    dados = bytesRecebidos.decode("utf-8")
    print(dados)

# Teste que realiza uma requisição de login com nome de usuário muito grande usando sendall # 
def teste_ReqLogin2(HOSTSC, PORTSC, socket):
    requisicao_servidor = {
        "operacao": "login",
        "username": 64000 * 'A',                        # mensagens de 64KB permitem testar a recepção chunk by chunk do Servidor Central
        "porta": 25641
    }
    requisicaoJSON = json.dumps(requisicao_servidor)
    # Prepara o envio da requisição
    tamRequisicao = len(requisicaoJSON)
    tamReqBytes = tamRequisicao.to_bytes(2, "big")
    socket.sendall(tamReqBytes)
    bytesEnviados = bytes(requisicaoJSON, "utf-8")
    socket.sendall(bytesEnviados)
    
    # Prepara a recepção da resposta
    first2Bytes = socket.recv(2)
    tamResposta = int.from_bytes(first2Bytes, "big")
    bytesRecebidos = socket.recv(tamResposta + 1024)    # Recebe como resposta o tamResposta + 1KB de auxílio
    
    dados = bytesRecebidos.decode("utf-8")
    print(dados)

# Teste que realiza uma requisição de login com nome de usuário muito grande usando o send # 
def teste_ReqLogin3(HOSTSC, PORTSC, socket):
    requisicao_servidor = {
        "operacao": "login",
        "username": 64000 * 'B',                        # mensagens de 64KB permitem testar a recepção chunk by chunk do Servidor Central
        "porta": 25641
    }
    requisicaoJSON = json.dumps(requisicao_servidor)
    # Prepara o envio da requisição
    tamRequisicao = len(requisicaoJSON)
    tamReqBytes = tamRequisicao.to_bytes(2, "big")
    socket.send(tamReqBytes)
    bytesEnviados = bytes(requisicaoJSON, "utf-8")
    socket.send(bytesEnviados)
    
    # Prepara a recepção da resposta
    first2Bytes = socket.recv(2)
    tamResposta = int.from_bytes(first2Bytes, "big")
    bytesRecebidos = socket.recv(tamResposta + 1024)    # Recebe como resposta o tamResposta + 1KB de auxílio
    
    dados = bytesRecebidos.decode("utf-8")
    print(dados)

# Teste que realiza uma requisição de login errado - No JSON, Username e Porta estão com as iniciais maiúsculas # 
def teste_ReqLogin4(HOSTSC, PORTSC, socket):
    requisicao_servidor = {
        "operacao": "login",
        "Username": 64000 * 'B',                        # mensagens de 64KB permitem testar a recepção chunk by chunk do Servidor Central
        "Porta": 25641
    }
    requisicaoJSON = json.dumps(requisicao_servidor)
    # Prepara o envio da requisição
    tamRequisicao = len(requisicaoJSON)
    tamReqBytes = tamRequisicao.to_bytes(2, "big")
    socket.send(tamReqBytes)
    bytesEnviados = bytes(requisicaoJSON, "utf-8")
    socket.send(bytesEnviados)
    
    # Prepara a recepção da resposta
    first2Bytes = socket.recv(2)
    tamResposta = int.from_bytes(first2Bytes, "big")
    bytesRecebidos = socket.recv(tamResposta + 1024)    # Recebe como resposta o tamResposta + 1KB de auxílio
    
    dados = bytesRecebidos.decode("utf-8")
    print(dados)

def teste_ReqLista(HOSTSC, PORTSC, socket):
    requisicao_servidor = {
        "operacao": "get_lista"
    }
    requisicaoJSON = json.dumps(requisicao_servidor)
    tamRequisicao = len(requisicaoJSON)
    tamReqBytes = tamRequisicao.to_bytes(2, "big")
    
    
    socket.sendall(tamReqBytes)
    bytesEnviados = bytes(requisicaoJSON, "utf-8")
    socket.sendall(bytesEnviados)
    
    first2Bytes = socket.recv(2)
    tamResposta = int.from_bytes(first2Bytes, "big")
    
    bytesRecebidos = socket.recv(tamResposta + 1024)
    dados = str(bytesRecebidos, "utf-8")
    print(dados)
    
# Método para fazer logoff num usuário em determinado Server
def fazLogoff(HOSTSC, PORTSC, socket, username):
    requisicao_servidor = {
        "operacao": "logoff",
        "username": username
    }
    requisicaoJSON = json.dumps(requisicao_servidor)
    tamRequisicao = len(requisicaoJSON)
    tamReqBytes = tamRequisicao.to_bytes(2, "big")
    
    socket.sendall(tamReqBytes)
    bytesEnviados = bytes(requisicaoJSON, "utf-8")
    socket.sendall(bytesEnviados)
        
    first2Bytes = socket.recv(2)
    tamResposta = int.from_bytes(first2Bytes, "big")
    
    bytesRecebidos = socket.recv(tamResposta + 1024)
    dados = str(bytesRecebidos, "utf-8")
    print(dados)


def main():
    #HOSTSC = input("IP SC: ")
    #PORTSC = input("PORTSC: ")
    HOSTSC = "10.11.0.38"
    PORTSC = 9001
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOSTSC,int(PORTSC)))
   
    
    teste_ReqLogin4(HOSTSC, PORTSC, sock)
    

main()
