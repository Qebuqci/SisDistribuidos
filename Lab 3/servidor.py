# -*- encoding: utf-8 -*-

import socket
from collections import Counter

import select
import sys

import threading

# 0. Constantes
COD_ERR = -1
QNT_CONEXOES = 5

entradas = [sys.stdin]  #define a lista de I/O de interesse (jah inclui a entrada padrao)
conexoes = {}           #armazena as conexoes ativas
lock = threading.Lock() #lock para acesso do dicionario 'conexoes'

# 1. Parâmetros da conexão
HOST = ''
PORTA = 7002

# Cria um socket de servidor e o coloca em modo de espera por conexoes
# Entrada:
# Saida: o socket criado'''
def iniciarServidor():
    # Criar descritor de socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Pilha TCP/IP, TCP 

    # Interliga tal descritor com os parâmetros da conexão definidos
    sock.bind((HOST, PORTA))

    # Coloca-se em modo de espera (escuta) por conexao
    print("Servidor em escuta...Aguardando conexões")
    sock.listen(QNT_CONEXOES) # argumento indica a qtde maxima de conexoes pendentes

    # configura o socket para o modo nao-bloqueante
    sock.setblocking(False)
    
    # inclui o socket principal na lista de entradas de interesse
    entradas.append(sock)

    return sock

# Aceita o pedido de conexao de um cliente
# Entrada: o socket do servidor
# Saida: o novo socket da conexao e o endereco do cliente
def aceitarConexao(sock):
    novoSock, endereco = sock.accept() # estabelece conexao com o proximo cliente
    print('Conectado com: ', endereco) # imprime endereço do cliente conectado

    # registra a nova conexao
    lock.acquire()
    conexoes[novoSock] = endereco 
    lock.release()
    
    return novoSock, endereco

# Recebe mensagens e as envia de volta para o cliente (ate o cliente finalizar)
# Entrada: socket da conexao e endereco do cliente
# Saida:
def atenderRequisicoes(novoSock, endereco):
    while True:
        data = novoSock.recv(1024)  #recebe dados do cliente
        if not data: # dados vazios: cliente encerrou
            print(str(endereco) + '-> encerrou')
            lock.acquire()
            del conexoes[novoSock] #retira o cliente da lista de conexoes ativas
            lock.release()
            novoSock.close() # encerra a conexao com o cliente
            return 
        nomeArq = str(data, 'utf-8')
        listagem = contarOcorrencias(nomeArq)
        resposta_cliente = bytes(listagem, 'utf-8') # prepara uma resposta para o cliente
        novoSock.send(resposta_cliente)

# Busca um arquivo no diretório local pelo nome
# Entrada: String Nome do Arquivo
# Saída: Um codigo de erro, em caso de arquivo inexistente ou o conteudo do arquivo como uma String
def buscarArquivo(nomeArquivo):
    try:
        arquivo = open(nomeArquivo, 'r').read()
        return arquivo
    except:
        return COD_ERR
        
# Conta as Ocorrencias das 5 palavras mais citadas no arquivo de entrada
# Entrada: String nome do arquivo
# Saída: Um código de erro, em caso de arquivo inexistente ou a listagem das 5 palavras de maior ocorrencia
def contarOcorrencias(nomeArquivo):
    busca_dados = buscarArquivo(nomeArquivo)
    if busca_dados == COD_ERR:
        return str(COD_ERR)
    palavras = busca_dados.split() # Todas as palavras do arquivo
    contadas = Counter(palavras)   # Contagem de ocorrencias de todas as palavras do arquivo
    maior_ocorrencia = contadas.most_common(5) # Listagem das 5 palavras de maior ocorrencia
    return str(maior_ocorrencia)

def main():
    sock = iniciarServidor()
    while True:
        leitura, escrita, excecao = select.select(entradas, [], []) #espera por qualquer entrada de interesse
        #tratar todas as entradas prontas
        for pronto in leitura:
            if pronto == sock:
                novoSock, endereco = aceitarConexao(sock)
                print("Aguardando por nome de arquivo...")
                conexoes[novoSock] = endereco
                cliente = threading.Thread(target=atenderRequisicoes, args = (novoSock, endereco))
                cliente.start()
            elif pronto == sys.stdin:
                cmd = input()
                if cmd == str(COD_ERR):
                    if not conexoes: #somente termina quando nao houver clientes ativos
                        # Encerra os descritores de socket
                        sock.close()
                        sys.exit(0)
                    else:
                        print("ha conexoes ativas")
                    
main()
    
