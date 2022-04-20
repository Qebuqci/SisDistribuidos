# Ativo: Cliente de echo
# -*- encoding: utf-8 -*-

import socket

# 0. Constantes 
COD_END = "encerrar,-1"

# 1. Parâmetros da Conexão
HOST = 'localhost'
PORTA = 7555

# 2. Cria um descritor de Conexão
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Pilha TCP/IP, TCP 

# 3. Conecta-se com o lado passivo (servidor de echo)
sock.connect((HOST, PORTA)) 

while True:
    msg = input('Digite uma mensagem para o servidor: ')
    # 4. Envia uma mensagem digitada para o servidor
    sock.send(bytes(msg, 'utf-8'))
    # 5. espera a resposta do servidor (chamada pode ser BLOQUEANTE)
    ack = sock.recv(1024) # argumento indica a qtde maxima de bytes da mensagem
    # 6. imprime mensagem
    print('ACK: ' + str(ack,  encoding='utf-8')) 
    if str(ack, "utf-8") == COD_END:
        print("ACK: Comando de encerrar retornado! Encerrando cliente") # imprime encerramento
        break

# 7. encerra a conexao
sock.close() 
