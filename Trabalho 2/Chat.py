# -*- encoding: utf-8 -*-

''' Classe Chat, que armazena informações sobre um chat (sala).
    Usada como auxílio pelas demais classes da aplicação.
'''

class Chat():
    def __init__(self, chatname, clientOwner, tSenha = False):
        self.chatname = chatname
        self.owner = clientOwner
        self.senha = tSenha        
        
        # Dicionário com a mesma estrutura do self.connections do Servidor, só que armazena clientes conectadas num chat. 
        self.connecteds = {} # Key: nickname. Value: [ip, porta]
        
        self.msg_history = ""
        
    def dadosChat(self):
        dados = {
            'chatname': self.chatname,
            'criador': self.owner,
            'senha': self.senha
        }
        return dados

    def conectar(self, clientname, ip_cliente, porta_cliente):
        print(f'<chat: {self.chatname} - usuario conectado: {clientname, ip_cliente, porta_cliente}>')
        self.connecteds[clientname] = [ip_cliente, porta_cliente]

    def desconectar(self, clientname):
        self.connecteds.pop(clientname)

    def membros(self):
        return self.connecteds

    def historico(self):
        return self.msg_history

    def novaMsg(self, msg, clientname):
        self.msg_history += clientname + ': ' + msg + '\n'
