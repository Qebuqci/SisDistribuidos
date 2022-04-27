# -*- encoding: utf-8 -*-

import socket

# 0. Constantes
COD_ERR = -1

# 1. Parâmetros da Conexão
HOST = ''
PORTA = 5000

# 2. Criar descritor de socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Pilha TCP/IP, TCP 

# 3. Conectar ao servidor
sock.connect((HOST, PORTA))

# Função que implementa a interface em linha de comando da aplicação #
# Entrada: String nomeArquivo, descritor de socket da conexão feita.
# Saída: 
def CLI_usuario(nomeArquivo, sock):
    sock.send(bytes(nomeArquivo, 'utf-8'))
    resposta_servidor = sock.recv(1024) # recebe a resposta do servidor
    if (str(resposta_servidor), 'utf-8') == COD_ERR:
        return COD_ERR
    
    print("# Lista de palavras ordenadas com suas respectivas contagens")
    #print(str(resposta_servidor, 'utf-8'))
    print(resposta_servidor.decode('utf-8'))

# 4. Chamar a função CLI_usuario
while True:
    arq = input("Digite o nome do arquivo: ")
    if CLI_usuario(arq, sock) == COD_ERR:
        break
    
# 5. Fechar descritor de socket
sock.close()
