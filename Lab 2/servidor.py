# -*- encoding: utf-8 -*-

import socket
from collections import Counter

# 0. Constantes
COD_ERR = -1

# 1. Parâmetros da conexão
HOST = ''
PORTA = 5000

# 2. Criar descritor de socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Pilha TCP/IP, TCP 

# 3. Interliga tal descritor com os parâmetros da conexão definidos
sock.bind((HOST, PORTA))

# 4. Coloca-se em modo de espera (escuta) por conexao
print("Servidor em escuta...Aguardando por 1 conexão")
sock.listen(1) # argumento indica a qtde maxima de conexoes pendentes

# 5. Aceita a primeira conexao da fila (chamada pode ser BLOQUEANTE)
novoSock, endereco = sock.accept() # retorna um novo socket e o endereco do par conectado
print('Conectado com: ', endereco) # imprime endereço do cliente conectado

# Busca um arquivo no diretório local pelo nome
# Entrada: String Nome do Arquivo
# Saída: Um codigo de erro, em caso de arquivo inexistente ou o conteudo do arquivo como uma String
def buscaArquivo(nomeArquivo):
    try:
        arquivo = open(nomeArquivo, 'r').read()
        return arquivo
    except:
        return COD_ERR
        
# Conta as Ocorrencias das 5 palavras mais citadas no arquivo de entrada
# Entrada: String nome do arquivo
# Saída: Um código de erro, em caso de arquivo inexistente ou a listagem das 5 palavras de maior ocorrencia
def contaOcorrencia(nomeArquivo):
    busca_dados = buscaArquivo(nomeArquivo)
    if busca_dados == COD_ERR:
        return COD_ERR
    palavras = busca_dados.split() # Todas as palavras do arquivo
    contadas = Counter(palavras)   # Contagem de ocorrencias de todas as palavras do arquivo
    maior_ocorrencia = contadas.most_common(5) # Listagem das 5 palavras de maior ocorrencia
    return str(maior_ocorrencia)
        
while True:
    print("Aguardando por nome de arquivo...")
    requisicao_cliente = novoSock.recv(1024) # recebe a requisicao do cliente
    if str(requisicao_cliente, 'utf-8') == COD_ERR:
        break
    nomeArq = str(requisicao_cliente, 'utf-8')
    listagem = contaOcorrencia(nomeArq)
    print(type(listagem))
    resposta_cliente = bytes(listagem, 'utf-8') # prepara uma resposta para o cliente
    novoSock.send(resposta_cliente)
    
# Encerra os descritores de socket
novoSock.close()
sock.close()
    
