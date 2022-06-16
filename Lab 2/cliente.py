# -*- encoding: utf-8 -*-

import socket

# 0. Constantes
COD_ECR = -1                                                # define um código de encerramento
COD_NARQ = -2                                               # define um código para arquivo não encontrado

# 1. Parâmetros da Conexão
HOST = 'localhost'
PORTA = 5002

# 2. Criar descritor de socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    # Pilha TCP/IP, TCP 

# 3. Conectar ao servidor
sock.connect((HOST, PORTA))

# Função que implementa a interface em linha de comando da aplicação #
# // Entrada: Descritor de socket da conexão feita.
def CLI_usuario():
    while True:
        nomeArquivo = input("Nome do arquivo: ")            # Entrada
        if nomeArquivo == '' or nomeArquivo == '\n': 
            continue
        sock.send(bytes(nomeArquivo, 'utf-8'))            # Envia o nome
        resposta_servidor = sock.recv(1024)               # Resposta do servidor
        resposta_servidorString = resposta_servidor.decode("utf-8")
        
        if resposta_servidorString == str(COD_NARQ):
            print("Arquivo não encontrado")
            continue                                        
        elif resposta_servidorString == str(COD_ECR):
            print("Servidor encerrado\nEncerrando cliente...")
            break
        else:
            print("# Lista de palavras ordenadas com suas respectivas contagens")
            print(resposta_servidorString)                      

# 4. Chamar a função CLI_usuario
CLI_usuario()
# 5. Fechar descritor de socket
sock.close()
