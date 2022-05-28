# -*- encoding: utf-8 

import json, socket, threading
import RichTextOnTerminal

'''
Classe auxiliar a Interface que lida com a comunicação entre os pares (peers)
'''

class PeerToPeer:
    
    # Construtor da Classe #
    # // Entrada: Um host,porta,nConexoes para aguardar conexões de outros peers (modo escuta ou passivo)
    def __init__(self, host, porta, nConexoes):
        self.host = host
        self.porta = porta
        self.nConexoes = nConexoes
        self.cor = RichTextOnTerminal.RichTextOnTerminal()
        
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.bind((self.host, self.porta))
        print(self.cor.tciano() + self.cor.tnegrito() + self.cor.tsublinhado() + "Aplicação aguardando peers..." + self.cor.end())
        self.sock.setblocking(False)
        # Constroi a instância (já) em modo de escuta (Servidor de Peers para aceitar outros pares)
        self.sock.listen(self.nConexoes)
                        
    # Método que aceita as conexões do modo de escuta (passivo)
    def aceitarConexoes(self):
        peerSock, endereco = self.sock.accept()
        print("Conectado com: ", endereco)
        return (peerSock, endereco)
               
    # Método executado pelas threads para receber e imprimir as mensagens dos peers para o usuário final (sob um username) #
    # // Entrada: peerSock cuja thread executará o receive e o endereco desse peer
    def receberMensagem(self, peerSock, endereco):
        while True:
            bytesRecebidos = peerSock.recv(1024)
            dados = str(bytesRecebidos, "utf-8")
            dadosDict = json.loads(dados) # JSON to Dict (Hashmap)
            username = dadosJSON["username"]
            mensagem = dadosJSON["mensagem"]
            print(self.cor.tvermelho() + self.cor.tnegrito + "@" + self.cor.end() + self.cor.tamarelo + username + self.cor.end() + ': ' + mensagem)
    
    # Método que designa um socket entre o usuário final e um peer online (comunicação ativa) #
    # // Entrada: peername (username do peer em que deseja-se conectar) e um HashMap (dict) com JSON contendo Endereco e Porta de tal peername
    def conectarPeer(self, peername, dictJSON):
        enderecoPeer = dictJSON["Endereco"]
        portaPeer = int(dictJSON["Porta"])
        self.sockAtivo = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sockAtivo.connect((enderecoPeer,portaPeer))
        print("Conectado com: ", enderecoPeer)
