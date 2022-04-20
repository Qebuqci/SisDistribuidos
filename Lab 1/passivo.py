# Passivo: Servidor de echo
# -*- encoding: utf-8 -*-

import socket

# 0. Constantes 
COD_END = "encerrar,-1"

# 1. Parâmetros da Conexão
HOST = 'localhost'
PORTA = 7555

# 2. Cria um descritor de Conexão
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Pilha TCP/IP, TCP como transporte

# 3. Interliga tal descritor com os parâmetros da conexão definidos
sock.bind((HOST, PORTA))

# 4. Coloca-se em modo de espera (escuta) por conexao
print("Servidor em escuta...Aguardando por 1 conexão")
sock.listen(1) # argumento indica a qtde maxima de conexoes pendentes

# 5. Aceita a primeira conexao da fila (chamada pode ser BLOQUEANTE)
novoSock, endereco = sock.accept() # retorna um novo socket e o endereco do par conectado
print('Conectado com: ', endereco) # imprime endereço do cliente conectado

while True:
    msg = novoSock.recv(1024) # argumento indica a qtde maxima de dados
    if str(msg, "utf-8") == COD_END: 
        print("Comando de encerrar recebido! Encerrando servidor.") # imprime msg de encerramento
        novoSock.send(bytes(COD_END, "utf-8")) # envia o código de encerramento de volta ao cliente
        break 
    else: 
        print('Mensagem enviada pelo cliente : ' + str(msg,  encoding='utf-8'))
    novoSock.send(msg) # ACK : echo da mensagem recebida
    
# 6.1 fecha o socket da conexao
novoSock.close() 
# 6.2 fecha o socket principal
sock.close() 
