# -*- encoding: utf-8 -*-

import rpyc, threading, cv2, pickle

''' Classe Cliente que conecta-se com Servidor Central e faz requisições 
    sobre seus chats gerenciados, via chamadas remotas de procedimento (RPyC).
'''

class Cliente(rpyc.Service):
    def __init__(self, ip_cliente, porta_cliente, ip_servidor, porta_servidor):
        self.ip_cliente = ip_cliente
        self.porta_cliente = porta_cliente
        self.ip_servidor = ip_servidor
        self.porta_servidor = porta_servidor
               
        # Variável booleana que guarda estado do cliente quanto a transmissão de vídeo.
        self.transmissao_video = False # True, caso on. False caso contrário
        
        # Dicionário que armazena outros clientes cujo vídeo está sendo recebido e renderizado para esse cliente num chat
        self.clientes_renderizados = {} # Key: clientname. Value: buffer vídeo desse cliente 
        
        # Dicionário que armazena as threads de videos renderizados (recepção de vídeo) de cada cliente
        self.threads_videosRenderizados = {} # Key: Clientname que transmite. Value: Thread designada ao mesmo que recebe 
        
        # Lock para garantir atomicidade (mutex) na transmissão de vídeo 
        self.lock = threading.Lock()
        
    # Métodos da classe que acessam o Servidor Central remotamente 
    
    # Inicializa conexão com Servidor Central usando RPyC #
    def _init_conexaoServidor(self): #try e except talvez
        self.conn = rpyc.connect(self.ip_servidor, self.porta_servidor)
        
    # Destroi a conexão com Servidor Central usando RPyC #
    def _destroy_conexaoServidor(self):
        self.conn.root.desRegistrarConexao(self.nickname)
    
    # Seta um nickname para um cliente e registra ele no Servidor, caso não exista outro cliente com esse nickname #
    # // Entrada: Nickname a ser setado
    # // Saída: True caso o cliente consiga se registrar ou False, caso o cliente com esse nickname já esteja registrado
    def setNickname(self, nickname):
        # Se o nickname ainda não está conectado no Servidor Central, então sete #
        if not self.conn.root.verificarNickname(nickname):
            self.nickname = nickname
        return self.conn.root.registrarConexao(nickname, self.ip_cliente, self.porta_cliente)
        
    # Verifica clientes conectados ao servidor através de um procedimento remoto RPyC #
    def verClientesConectados(self):
        return self.conn.root.verClientesConectados()
        
    # Verifica chats (salas) disponíveis para se juntar através de uma chamada remota RPyC # 
    def verChatsDisponiveis(self):
        return self.conn.root.verChatsDisponiveis()
    
    # Permite o cliente criar um chat através de uma chamada remota de procedimento RPyC #
    # // Entrada: Nome do chat a ser criado e uma senha, caso desejável
    # // Saída: True em caso de sucesso e False, caso contrário
    def criarChat(self, chatname, senha):
       return self.conn.root.criarChat(chatname, self.nickname, senha)
    
    # Permite o cliente acessar os dados de um chat, caso ele exista #
    # // Entrada: Nome do chat no qual deseja-se obter os dados
    # // Saída: Dados desse chat ou False, caso não exista um chat com esse nome
    def verificarDadosChat(self, chatname):
        return self.conn.root.verificarChat(chatname)
    
    # Permite o cliente entrar num chat através de uma chamada remota de procedimento RPyC #
    # // Entrada: Chatname e sua senha
    # // Saída: True ou False, caso o cliente consiga entrar no chat ou caso contrário
    def entrarChat(self, chatname, senha):
        return self.conn.root.entrarChat(chatname, self.nickname, senha)
    
    # Ver os membros de um chat #
    # // Entrada: Nome do chat em que deseja-se saber os membros
    # // Saída: Nome dos clientes membros desse chat
    def verMembrosChat(self, chatname):
       return self.conn.root.membrosChat(chatname)
    
    # Verifica o histórico de mensagens do chat #
    # // Entrada: Nome do chat no qual deseja-se o histórico
    # // Saída: Histórico de mensagens desse chat
    def verHistoricoChat(self, chatname):
        return self.conn.root.historicoChat(chatname)
    
    # Sai de um chat (sala) #
    # // Entrada: Nome do chat em que deseja-se sair
    def sairChat(self, chatname):
         self.conn.root.sairChat(chatname, self.nickname)
    
    # Método que aciona o Servidor a compartilhar uma mensagem de um cliente num chat (sala) #
    # // Entrada: Mensagem a ser compartilhada com os demais membros do chat, nome do chat (sala)
    def compartilharMsg(self, msg, chatname):
        self.conn.root.compartilharMsg(msg, chatname, self.nickname)   
    
    def _init_video(self, chatname):
        if not self.transmissao_video:
            thread_transmissaoVideo = threading.Thread(target = self.transmitirVideo, 
                                      args = (chatname, self.transferenciaVideoNumero) ) 
            self.threads_transmissaoVideo.append(thread_transmissaoVideo)
            thread_transmissaoVideo.start()
        
    # #
    def transmitirVideo(self, chatname):
        print('b')
        # Bloco atômico
        #self.lock.acquire()
        video = cv2.VideoCapture(0)
        
        # Verifica se o vídeo foi aberto
        if video.isOpened():
            print("Vídeo ON")
            self.transmissao_video = True
        else:
            print("< Não foi possível abrir o vídeo. Tente novamente >")
                
        # Enquanto houver transmissão
        while self.transmissao_video:
            img, frame = video.read()
 
            #print(transferenciaVideoNumero)
            # Converte os frames de vídeo para um stream (fluxo) de bytes
            frameBytes = pickle.dumps(frame)
            
            #print(frameBytes)
            # Camera do Cliente (transmissor)
            cv2.imshow("Transmitindo video", frame)
            
             # Tecla de atalho 'q' fecha a janela de vídeo
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            # Botão X da GUI fecha a janela de vídeo
            if cv2.getWindowProperty("Transmitindo video", cv2.WND_PROP_VISIBLE) < 1:
                break
            
            # "Converte" (Wrapper) o método exposed_compartilharVideo do SERVIDOR para um método assíncrono
            compartilharVideo_async = rpyc.async_(self.conn.root.compartilharVideo)
            # Envia assincronamente o fluxo de bytes (com os frames do vídeo) para o SERVIDOR
            compartilharVideo_async(self.nickname, chatname, frameBytes)
            
        # Libera o hardware (camera) de vídeo
        video.release()
        
        # Destroi todas as janelas OpenCV caso existam
        cv2.destroyAllWindows()
        
        # Desregistrar transmissão de video no Servidor
        interromperCompartilhamento_async = rpyc.async_(self.conn.root.interromperCompartilhamentoVideo)
        interromperCompartilhamento_async(self.nickname, chatname)
                
        # Vídeo OFF
        print("Vídeo OFF")
        self.transmissao_video = False
        #self.lock.release()
        # Fim do bloco atômico
             
    # Server Client 
    # Métodos do modo passivo do cliente, permitindo conexões RPyC de volta do Servidor Central com mesmo 
    
    # Inicializa modo passivo do cliente #
    def _init_modoPassivo(self):
        self.servidor_cliente = rpyc.ThreadedServer( Cliente(self.ip_cliente, self.porta_cliente, self.ip_servidor, self.porta_servidor), 
                                                    port = self.porta_cliente)
        print('-- < ServerClient - Cliente no modo passivo > --')
        self.servidor_cliente.start()
        
    # Método executado assim que uma conexão RPyC é estabelecida #
    def on_connect(self, conn):
        pass
    
    # Método que é executado assim que conexão RPyC é fechada #
    def on_disconnect(self, conn):
        pass
    
    # Desativa o modo passivo do cliente, não permitindo mais chamadas RPyC #
    def _destroy_modoPassivo(self):
        self.servidor_cliente.close()
    
    # Chamadas remotas de procedimento (métodos exposed) acessadas pelo Servidor Central 
        
    # Recebe e imprime uma mensagem de um outro cliente do chat 
    # // Entrada: Nome do cliente que enviou a mensagem e a mensagem  
    def exposed_receberMsg(self, clientname, msg):
        print(f'{clientname}: {msg}')
    
    # #
    def exposed_receberVideo(self, clientname, bufferVideo_cliente):
        cliente_renderizado = self.clientes_renderizados.get(clientname)
        if not cliente_renderizado:
                self.clientes_renderizados[clientname] = bufferVideo_cliente
                print("< Recepção de vídeo do cliente " + clientname +  " iniciada >")
                # Thread lançada para renderizar essa recepção 
                thread_video = threading.Thread(target = self.renderizarVideo, 
                                                args = (clientname,) ) # vírgula , pois chatname no args necessária!
                # Registra essa thread de renderização e recepção num dicionário, sob o nome desse cliente transmissor
                self.threads_videosRenderizados[clientname] = thread_video
                thread_video.start()
    
        # Atualiza o buffer dos clientes que já estão sendo renderizados
        self.clientes_renderizados[clientname] = bufferVideo_cliente
       
    # #
    def renderizarVideo(self, clientname):
        while True:
            # Receba o buffer de vídeo do cliente
            bufferVideo_cliente = self.clientes_renderizados.get(clientname)
            #print(bufferVideo_cliente)
            if bufferVideo_cliente:
                # Carrega o fluxo (stream) de bytes como um frame
                frame = pickle.loads(bufferVideo_cliente)           
                # Exibem os frames na janela do opencv 
                cv2.imshow("Transmissao de Video do usuario: " + clientname, frame)
                cv2.waitKey(1)
            else:
                break
            # Tenta fechar as janelas de recepção manualmente
            #try:
                # Tecla de atalho 'q' fecha a janela de vídeo
             #   if cv2.waitKey(1) & 0xFF == ord('q'):
              #      break
                
                # Botão X da GUI fecha a janela de vídeo
               # if cv2.getWindowProperty("Transmissao de Video do usuario: " + clientname, cv2.WND_PROP_VISIBLE) < 1:
                #    break
            # Caso não seja possível, elas já foram fechadas, então ignore os erros
            #except cv2.error:
             #   pass
    ##
    def exposed_interromperRenderizacao(self, clientname):
        print("< Recepção de vídeo do cliente: " + clientname + " encerrada >")
        # Desregistra a renderização de video desse cliente, caso não tenha sido feito
        self.clientes_renderizados.pop(clientname)
        # Fecha a janela do opencv que renderizava esta transmissão
        cv2.destroyWindow("Transmissao de Video do usuario: " + clientname)
        # Encerra sua thread de recepção e renderização
        thread_renderizacao = self.threads_videosRenderizados.get(clientname)
        # Remove essa thread do dicionário de threads de recepção e renderização
        self.threads_videosRenderizados.pop(clientname)
        thread_renderizacao.join()
        return 
        
# Interface da aplicação com usuário final 

# Exibe o menu da aplicação #
def menu():
    print("---------| Menu |---------")
    print("1 - Ver pessoas conectadas")
    print("2 - Ver chats")
    print("3 - Criar chat")
    print("4 - Entrar em um chat")
    print("0 - Sair")
    print("--------------------------")

# Exibe o menu do chat #    
def chatMenu():
    print("-----------| Menu do chat |-----------")
    print("/m - < Mostrar membros do chat >")
    print("/v - < Iniciar transmissão de vídeo  >")
    print("/h - < Mostrar histórico de mensagens >")
    print("/d - < Mostrar dados do chat >")
    print("/exit - < Para sair do chat >")
    print("---------------------------------------")

def main(IP_CLIENTE, PORTA_CLIENTE, IP_SERVIDOR, PORTA_SERVIDOR):
    # Instância um cliente
    cliente = Cliente(IP_CLIENTE, PORTA_CLIENTE, IP_SERVIDOR, PORTA_SERVIDOR)
    
    # Lista de threads de transmissão de vídeo
    threads_transmissaoVideo = []
    
    # Inicializa o Servidor do Cliente (Server Client) numa thread diferente da principal, 
    # para o Servidor conectar de volta via RPyC
    thread_servidorCliente = threading.Thread(target = cliente._init_modoPassivo)
    thread_servidorCliente.start()    
    
    # Inicializa conexão RPyC com Servidor
    cliente._init_conexaoServidor()
    print("< Bem vindo ao WebChat >")
    
    # Set nickname
    nickname = input("Digite seu nickname: ")
    while not cliente.setNickname(nickname):
        print('---------------------------------------')
        print("-- Nome já utilizado, escolha outro! --")
        print('---------------------------------------')
        nickname = input("Digite seu nickname: ")
      
    # Inicializa interface 
    menu()
    while True:
        try:
            escolha = int(input("Digite uma opção do menu: "))
        except ValueError:
            print('------------------------------')
            print("-- Opção do menu inválida! -- ")
            print('------------------------------')
            continue
        if escolha == 1:
            print(cliente.verClientesConectados())
        elif escolha == 2:
            print(cliente.verChatsDisponiveis())
        elif escolha == 3:
            chatname = input("Digite o nome do chat que deseja criar: ")
            deseja_senha = input("Deseja senha? (s) ou (any key for n): ")
            if deseja_senha == "s":
                senha = input("Digite a senha do chat: ")
            else:
                senha = False
            if cliente.criarChat(chatname, senha):
                print('---------------------------------')
                print("-- Chat criado com sucesso -- ")
                print('---------------------------------')
            else:
                print('-------------------------------------------------------')
                print("-- Chat já existente. Não foi possível criar o chat -- ")
                print('-------------------------------------------------------')
            menu()
        elif escolha == 4:
            chatname = input("Digite o nome do chat que deseja entrar: ")
            senha_digitada = False
                
            dadosChat = cliente.verificarDadosChat(chatname)
            # Se não existe dados para esse chat, então esse chat não existe
            if not dadosChat:
                print('----------------------')
                print("-- Chat não existe! --")
                print('----------------------')
                continue
                
            # Caso o chat exista, verifique se têm senha
            if dadosChat['senha'] != False:
                print('-------------------')
                print("-- Chat privado -- ")
                print('-------------------')
                senha_digitada = input("Digite a senha do chat para entrar: ")
                   
            # Se foi possível entrar no chat, então
            if cliente.entrarChat(chatname, senha_digitada):
                chatMenu()
                print(f'Conectado no chat: ({chatname})')
                while True:
                    msg = input()
                    if msg == "/m":
                        print('<membros>')
                        for membro in cliente.verMembrosChat(chatname): print(membro)
                        print('---------')
                    elif msg == "/v":
                        # Se o cliente não está transmistindo vídeo, então
                        if not cliente.transmissao_video:
                            cliente.transmitirVideo(chatname)
                            #print('a')
                            #thread = threading.Thread(target = cliente.transmitirVideo, args = (chatname, ))
                            #threads_transmissaoVideo.append(thread)
                            #cliente._init_video(chatname)
                    elif msg == "/h":
                        print('< chat atualizado >')
                        print(cliente.verHistoricoChat(chatname))
                        print('-------------------')
                    elif msg == "/d":
                        print('<dados chat>')
                        print(dadosChat)
                        print('------------')
                    elif msg == "/exit":
                        cliente.sairChat(chatname)
                        menu()
                        break
                    else:
                        cliente.compartilharMsg(msg, chatname)
            # Caso contrário, então a senha digitada foi inválida, que é o único motivo para rodar abaixo
            else:
                print('--------------------------------------------------')
                print("Senha inválida. Não foi possível entrar nesse chat")
                print('--------------------------------------------------')
        elif escolha == 0:
            cliente._destroy_conexaoServidor()
            cliente._destroy_modoPassivo()
            # Encerrando todas as threads lançadas para transmissão de vídeo
            for thread in threads_transmissaoVideo:
                thread.join()
                
            break
        else:
            print('------------------------------')
            print("-- Opção do menu inválida! -- ")
            print('------------------------------')
            continue
    

        
if __name__ == "__main__":
    IP_CLIENTE = "192.168.0.66"         # Set IP_CLIENTE 
    PORTA_CLIENTE = input("Digite sua porta: ")      # Set PORTA_CLIENTE
    IP_SERVIDOR = "192.168.0.66"        # Set IP_SERVIDOR
    PORTA_SERVIDOR = "5000"     # Set PORTA_SERVIDOR
    main(IP_CLIENTE, PORTA_CLIENTE, IP_SERVIDOR, PORTA_SERVIDOR)
                   
            
