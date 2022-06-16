# -*- encoding: utf-8 -*-

import socket
from collections import Counter                     # Faz o uso de uma biblioteca interna para contar as palavras

# 0. Constantes
COD_ECR = -1                                        # define um código de encerramento
COD_NARQ = -2                                       # define um código para arquivo não encontrado

# 1. Parâmetros da conexão
HOST = ''
PORTA = 5002

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

# Busca um arquivo no diretório local pelo nome #
# // Entrada: String Nome do Arquivo
# // Saída: Um codigo de erro, em caso de arquivo inexistente ou o conteudo do arquivo como uma String
def buscaArquivo(nomeArquivo):
    try:                                                # Tenta encontrar o arquivo
        arquivo = open(nomeArquivo, 'r').read()
        return arquivo                                  # retorna o conteúdo do arquivo como uma String
    except:                                             # Caso ocorra algum erro
        print("Arquivo não encontrado no servidor...")
        return COD_NARQ  
        
# Conta as Ocorrencias das 5 palavras mais citadas no arquivo de entrada #
# // Entrada: String nome do arquivo
# // Saída: Um código de erro, em caso de arquivo inexistente ou a listagem das 5 palavras de maior ocorrencia
def contaOcorrencia(nomeArquivo):
    busca_dados = buscaArquivo(nomeArquivo)
    if busca_dados == COD_NARQ:                         # Se a busca de dados receber um código de erro
        return str(COD_NARQ)                            # então retorne tal codigo como string
    palavras = busca_dados.split()                      # Todas as palavras do arquivo numa lista
    contadas = Counter(palavras)                        # Cria uma instância de Counter, passando palavras
    maior_ocorrencia = contadas.most_common(5)          # Usa um método do objeto acima p/ listagem das 5 palavras de maior ocorrencia
    return str(maior_ocorrencia)                        

# Função principal do programa #
def main():        
    while True:
        print("Aguardando por nome de arquivo...")
        requisicao_cliente = novoSock.recv(1024)        # recebe a requisicao do cliente, com nome do arquivo
        nomeArq = str(requisicao_cliente, 'utf-8')
        print("Nome recebido: " + nomeArq)
        if nomeArq == str(COD_ECR):                     # se o nomeArq for o código de encerramento
            print("Codigo de encerramento!")
            print("Encerrando servidor...")
            novoSock.send(bytes(str(COD_ECR),'utf-8'))  # envia pro cliente um codigo de encerramento
            break                                       # quebra o loop p/ encerrar o servidor
        listagem = contaOcorrencia(nomeArq)
        resposta_cliente = bytes(listagem, 'utf-8')     # prepara a resposta para o cliente
        novoSock.send(resposta_cliente)
        
if __name__ == "__main__":
    main()
    # Encerra os descritores de socket
    novoSock.close()
    sock.close()

    
