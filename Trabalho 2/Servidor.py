# -*- encoding: utf-8 -*-

import rpyc, cv2, pickle
from Chat import Chat

''' Classe Servidor, que armazena e gerencia chats e atua como HUB de um chat,
    repassando dados multimidia (mensagem ou vídeo) de um cliente emissor para
    os demais membros desse chats.
'''

class Servidor(rpyc.Service):
    def __init__(self, ip_servidor, porta_servidor):
        self.ip_servidor = ip_servidor
        self.porta_servidor = porta_servidor
        
        # Dicionário que armazena os clientes conectados no Servidor. 
        self.connections = {} # Key: clientname. Value: lista com [ip_cliente, porta_cliente]
        
        # Dicionário que armazena os chats disponiveis
        self.chats = {} # Key: chatname. Value: Object chat (instância da classe Chat)
        
        # Dicionário que armazena o buffer de vídeo de certos clientes num chat (sala)
        self.videoChat = {} # Key: Chatname. Value: Dicionário {clientname: bufferVideo }
                        
    # Inicializa o Servidor no modo passivo para receber conexões RPyC
    def _init_server(self):
        servidor = rpyc.ThreadedServer(Servidor(self.ip_servidor, self.porta_servidor), port = self.porta_servidor)
        print('----- < Server inicializado - Servidor no modo passivo > -----')
        servidor.start()
        
    # Método executado assim que uma conexão RPyC é estabelecida
    def on_connect(self, conn):
        pass
        
    # Método que é executado assim que conexão RPyC é fechada
    def on_disconnect(self, conn):
        pass

    # Chamadas remotas de procedimento (métodos exposed) acessadas pelo Cliente #      
    
    # Registra a conexão de um cliente na aplicação #
    # // Entrada: Nome do cliente a ser registrado, ip e porta dele
    # // Saída: True ou False, em caso de sucesso ou insucesso
    def exposed_registrarConexao(self, clientname, ip_cliente, porta_cliente):
        cliente_registrado = self.connections.get(clientname)
        if cliente_registrado:
            return False    # Não registra a conexão, pois já existe um clientname registrado
        else:
            self.connections[clientname] = [ip_cliente, porta_cliente]
            return True     # registra a conexão, pois não existe nenhum clientname registrado
    
    # Desregistra a conexão de um cliente na aplicação #
    # // Entrada: Nome do cliente a ser desregistrado
    def exposed_desRegistrarConexao(self, clientname):
        self.connections.pop(clientname)
    
    # Verifica se já existe um cliente conectado na aplicação sob certo nome de usuário #
    # // Entrada: Nome do cliente a ser verificado
    # // Saída: Dados desse cliente ou NoneType object, em caso de sucesso ou insucesso
    def exposed_verificarNickname(self, clientname):
        return self.connections.get(clientname)
    
    # Retorna todos os clientes conectados na aplicação #
    def exposed_verClientesConectados(self):
        return self.connections
    
    # Retorna todos os chats criados na aplicação # 
    def exposed_verChatsDisponiveis(self):
        return self.chats
    
    # Cria um novo chat #
    # // Entrada: Nome do chat (sala) a ser criado, Nome do cliente dono desse chat e uma senha
    # // Saída: True ou False, em caso de sucesso ou insucesso
    def exposed_criarChat(self, chatname, clientname, senha):
        chat_existente = self.chats.get(chatname)
        # Se o chat existe, então
        if chat_existente:
            return False   
        
        # Caso contrário
        chat = Chat(chatname, clientname, senha)
        self.chats[chatname] = chat
        print(f'<chat criado: {chatname}>')
        return True
 
    # Verifica dados de um chat #
    # // Entrada: nome do chat em que deseja-se obter dados
    # // Saída: dados do chat, caso esse chat exista ou False, caso ele não exista  
    def exposed_verificarChat(self, chatname):
        chat_existente = self.chats.get(chatname)
        # Se o chat não é existente, então
        if not chat_existente:
            return False
        
        # Caso contrário, o chat existe, então retorne seus dados
        return chat_existente.dadosChat()
    
    # Registra um cliente num chat #
    # // Entrada: Nome do chat em que deseja-se entar, nome do cliente que está entrando e a senha do chat
    # // Saída: True ou False em caso de sucesso ou insucesso, no registro desse cliente no chat (sala)
    def exposed_entrarChat(self, chatname, clientname, senha):
        chat = self.chats.get(chatname)
        dadosChat = chat.dadosChat()
        if dadosChat['senha'] != senha:
            return False
          
        # Caso contrário, registra o cliente nesse chat
        cliente = self.connections.get(clientname)
        ip_cliente, porta_cliente = cliente[0], cliente[1]
        
        # Registra conexão de um cliente no chat existente 
        chat.conectar(clientname, ip_cliente, porta_cliente)
        return True
        
    # Retorna o histórico de mensagens do chat #
    # // Entrada: Nome do chat
    # // Saída: Histórico de mensagens
    def exposed_historicoChat(self, chatname):
        return self.chats.get(chatname).historico()
        
    # Retorna todos membros de um chat (sala) #
    # // Entrada: Nome do chat que deseja-se obter seus membros
    # // Saída:  Nome dos clientes membros desse chat
    def exposed_membrosChat(self, chatname):
        return self.chats.get(chatname).membros()
    
    # Compartilha mensagem enviada de um cliente entre os demais membros de um chat (sala) #
    # // Entrada: Mensagem a ser compartilhada, nome do chat que tal mensagem foi enviada e o nome do cliente emissor
    def exposed_compartilharMsg(self, msg, chatname, clientname):
        chat = self.chats.get(chatname)
        chat.novaMsg(msg, clientname)
        membros_chat = chat.membros()
        for membro in membros_chat:
            if membro != clientname:
                ip_membro, porta_membro = membros_chat.get(membro)[0], membros_chat.get(membro)[1]
                # Estabelece uma conexão temporária de volta do Servidor com Cliente
                connTemp_back = rpyc.connect(ip_membro, porta_membro)
                connTemp_back.root.receberMsg(clientname, msg)
                connTemp_back.close()
    
    def exposed_compartilharVideo(self, clientname, chatname, frameBytes):
        if not self.videoChat.get(chatname) or clientname not in self.videoChat.get(chatname):
            # Armazena pela primeira vez os frames de vídeo de um cliente do chat num buffer
            self.videoChat[chatname] = {clientname : frameBytes}
            print("< Compartilhando vídeo de " + clientname + " no chat: " + chatname + " >")
        
        print("teste")
        # Atualiza esse buffer
        self.videoChat[chatname] = {clientname : frameBytes}
        # Resgata o chat (object) disponíveis no Servidor, com o chatname 
        chat = self.chats.get(chatname)
        # Encontra outros membros dentro desse chat
        membros_chat = chat.membros()
        # Compartilha video para outros membros desse chat (sala), com exceção do cliente (clientname)
        for membro in membros_chat:
            if membro != clientname:
                ip_membro, porta_membro = membros_chat.get(membro)[0], membros_chat.get(membro)[1]
                connTemp_back = rpyc.connect(ip_membro, porta_membro)
                # "Converte" (Wrapper) o método exposed recebeVideo do Cliente para um método assíncrono
                receberVideo_async = rpyc.async_(connTemp_back.root.receberVideo)
                for cliente_transmissor in self.videoChat.get(chatname):
                    # Envie assincronamente o buffer de frames de vídeo desse transmissor para todos os demais membros do chat (sala)
                    bufferVideo_cliente = self.videoChat.get(chatname).get(cliente_transmissor)
                    receberVideo_async(cliente_transmissor, bufferVideo_cliente)  
                
    def exposed_interromperCompartilhamentoVideo(self, clientname, chatname):
        print("< Compartilhamento de vídeo do cliente: " + clientname + " no chat: " + chatname + " interrompido >")
        # Desregista clietname dos transmissores de vídeo do chat
        self.videoChat.get(chatname).pop(clientname)
        # Resgata o chat (object) disponíveis no Servidor, com o chatname 
        chat = self.chats.get(chatname)
        # Encontra outros membros dentro desse chat
        membros_chat = chat.membros()
        # Interrompe a renderização assincronamente para todos os demais membros do chat
        for membro in membros_chat:
            if membro != clientname:
                ip_membro, porta_membro = membros_chat.get(membro)[0], membros_chat.get(membro)[1]
                connTemp_back = rpyc.connect(ip_membro, porta_membro)
                interromperRenderizacao_async = rpyc.async_(connTemp_back.root.interromperRenderizacao)
                interromperRenderizacao_async(clientname)
    
    # Desconecta um cliente de um chat #
    # // Entrada: Nome do chat em que o cliente se encontra e o nome do cliente
    def exposed_sairChat(self, chatname, clientname):
        chat = self.chats.get(chatname)
        chat.desconectar(clientname)

def main(IP_SERVIDOR, PORTA_SERVIDOR):
    servidor = Servidor(IP_SERVIDOR, PORTA_SERVIDOR)
    servidor._init_server()

if __name__ == "__main__":
    IP_SERVIDOR = "192.168.0.66"        # Set IP_SERVIDOR
    PORTA_SERVIDOR = "5000"             # Set PORTA_SERVIDOR
    main(IP_SERVIDOR, PORTA_SERVIDOR)
