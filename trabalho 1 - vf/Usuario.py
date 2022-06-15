# -*- enconding: utf-8

import socket, json, sys, select, threading, random
import RichTextOnTerminal

'''
Usuario final do chat distribuído - A classe têm três funcionalidades:
1. Comunicação com Servidor Central, enviando requisições e recebendo respostas
2. Interfaceamento com usuário final, através do processamento de comandos de entrada
3. Comunicação P2P com outros usuários finais disponíveis (online) no Servidor Central
'''

class Usuario:
    # Parâmetros da classe (variáveis globais) - úteis para compartilhar dados entre threads da classe (um processo no SO)
    
    threads_p2p = []          # Lista que armazena as threads P2P do sistema (ativas por usuario) 
    
    # HashMap (dict) para armazenar informações dos peers conectados
    # Estrutura do dict: {endereco : {"username": USERNAME, "socket": SOCKET, "porta": PORTA, "cor": COR} }
    peersConectados = {}      # endereco é a chave e seu valor associado é outro dict com chaves username, socket, porta e COR
  
    lock = threading.Lock()   # Lock para evitar condições de corrida nas variáveis acima (no dicionário peersConectados) e COND_EXIT
    
    Logado = False            # Variável booleana que guarda o estado do usuario quanto ao login no SC. Online = True, Off = False
    
    # Construtor da Classe - argumentos locais (sem a necessidade de serem vistos por todas as threads)
    # // Entrada: Um host,porta,nConexoes para aceitar peers e HOSTSC,PORTASC do Servidor Central (para requisições)
    def __init__(self, host, porta, nConexoes, HOSTSC, PORTASC):
        self.host = host
        self.porta = porta
        self.nConexoes = nConexoes
        
        self.hostsc = HOSTSC
        self.portasc = PORTASC
        
        self.username = ""       # nickname (ou username) ativo no Servidor Central
        
        # HashMap (dicionário) que armazena a lista de usuários online (resposta do SC) conforme especificado
        # Estrutura do dict: {username : {"Endereco": IP, "PORTA": porta} }, onde IP e porta são strings 
        self.usuariosOnline = {}    # username é chave e seu valor associado é outro dict com chaves ENDERECO e PORTA 
        
        # socket que faz a comunicação com Servidor Central, para enviar e receber requisições através dele
        self.sockServidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
        # socket que se mantêm em modo passivo, atuando como servidor de peers (outros usuarios que queiram se conectar)
        self.sockPassivo_p2p = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
        self.cor = RichTextOnTerminal.RichTextOnTerminal()  # instância rich text (deixa o texto mais rico)
        self.entradas = [sys.stdin]                         # Inclui o stdin na lista de entradas que aguardam I/O do socket
    
    
    # ----------------------------- Métodos multifuncionais (auxiliares a varias funcionalidades) ---------------------------- #
    
    # Método usado pelas funcionalidades 1 e 3 (Comunicação com Servidor Central e Peer to Peer) para converter a msg em bytes #
    # // Entrada: Uma string Msg a ser convertida em bytes
    # // Saída: 2 bytes (formato BigEndian) no inicio indicando o tamanho de Msg (+) concatenado com (+) a mensagem em bytes
    def msgToBytes(self, msg):
        tamanhoMsg = len(msg)   
        tamMsgBytes = tamanhoMsg.to_bytes(2, "big")         # Tamanho da mensagem convertido em 2 bytes BigEndian
        #msg2Bytes = bytes(msg, "utf-8")
        msgInBytes = msg.encode("utf-8")                    # String Mensagem em bytes
        return tamMsgBytes + msgInBytes                     # Concatena dois Bytes
                
    # Método usado pelas funcionalidades 1 e 3 (Comunicação com Servidor Central e Peer to Peer) para receber chunks e converter 
    # em mensagem (string) #
    # // Entrada: O tamanho da Msg a ser recebida e o socket pelo qual será recebida
    # // Saída: Uma string msg decodificada dos bytes recebidos em pieces (chunks)
    def ChunksRecebidosToMsg(self, TamMsg, socket):
        minBuffer = 10                                      # buff mínimo de 10 bytes p/ garantir que seja todo preenchido
        chunksRecebidos = socket.recv(TamMsg)               # Recebe o buffer do tamanho da mensagem
        msg = chunksRecebidos.decode("utf-8")               # Decodifica os bytes dessa informação em String 
        while len(msg) < TamMsg:                            # Verifica se o tamanho da String é menor que o tamanho da mensagem
            chunksRecebidos = socket.recv(minBuffer)        # Caso seja, recebe a mensagem em chunks (partes) de 10 bytes cada
            #print("Recebidos : " + str(len(msg)))
            msg += chunksRecebidos.decode("utf-8")          # Vai decodificando e inserindo na string msg recebida
                   
        return msg                                          # retorna a mensagem 

    # ---------------------------------- Funcionalidade 1. Comunicação com Servidor Central ---------------------------------- #
    
    # Faz a conexão da aplicação do usuário final com Servidor Central #
    def conectarServCentral(self):
        try:    # Tenta se conectar
            self.sockServidor.connect((self.hostsc, self.portasc))
            print(self.cor.tazul() + " Conexão com Servidor Central Estabelecida ! " + self.cor.end())
        except: # Caso ocorra alguma exceção, aplicação encerra
            print(self.cor.tvermelho() + self.cor.tnegrito() + " Erro ao se conectar com Servidor Central ! " + self.cor.end())
            self.quit()
            sys.exit(0) # Parâmetro 0 no exit para indicar que o encerramento foi correto
    
    # Faz a requisição de login no Servidor Central sob o nickname (username) definido #
    def requisitarLogin(self):
        requisicao_servidor = {
            "operacao": "login",
            "username": self.username,
            "porta": self.porta
        }
        requisicaoJSON = json.dumps(requisicao_servidor)    # Monta a string no formato JSON do dicionario requisicao_servidor
        
        reqBytes = self.msgToBytes(requisicaoJSON)
        self.sockServidor.sendall(reqBytes)                 # Envia os bytes da requisicao
        self.receberResposta()
        
    # Faz a requisição de logoff no Servidor Central sob o username atual, permitindo trocá-lo #
    def requisitarLogoff(self):
        requisicao_servidor = {
            "operacao": "logoff",
            "username": self.username
        }
        requisicaoJSON = json.dumps(requisicao_servidor)    # Monta a string no formato JSON do dicionario requisicao_servidor
        
        reqBytes = self.msgToBytes(requisicaoJSON)
        self.sockServidor.sendall(reqBytes)                 # Envia os bytes da requisicao
        self.receberResposta()
    
    # Faz a requisição da lista de usuários online (disponíveis) para iniciar uma conversa #
    def requisitarLista(self):
        requisicao_servidor = {"operacao": "get_lista"}
        requisicaoJSON = json.dumps(requisicao_servidor)    # Monta a string no formato JSON do dicionario requisicao_servidor
        
        reqBytes = self.msgToBytes(requisicaoJSON)
        self.sockServidor.sendall(reqBytes)                 # Envia os bytes da requisicao
        self.receberResposta()
    
    # Método único que recebe e imprime a resposta (p/ usuário final) de cada requisição acima # 
    def receberResposta(self):
        tamRespostaBytes = self.sockServidor.recv(2)        # Recebe os 2 primeiros bytes

        #if not tamRespostaBytes:                            # Se não receber, Servidor encerrou
        #    self.quit()                                     # encerre a aplicação corretamente com um comando da funcionalidade de Interface
        # ele so chama receberResposta depois que faz uma requisição, então necessariamente ele  aguarda por dados
        # isso aqui não tem jeito, de controlar. Se o servidor de alguém não enviar dados, então a aplicação simplesmente trava.
        # A maneira de contornar isso seria designar uma thread ou usar um select para aguardar I/O inteligentemente
        # mas da maneira como foi feito, a comunicação com servidor central por parte do usuário ocorre iterativamente. Dsse jeito, não tem jeito
       
        # Caso receba
        tamRespInt = int.from_bytes(tamRespostaBytes, "big")        # Dos (from) 2 primeiros bytes em BigEndian converta para inteiro        

        #dados = self.ChunksRecebidosToMsg(tamRespInt, self.sockServidor)
        
        bytesRecebidos = self.sockServidor.recv(tamRespInt + 1024)   # Recebe o tamanho da Mensagem + 1KB de auxílio           
        dados = bytesRecebidos.decode("utf-8")              
        
        try:
            dadosJSON = json.loads(dados)
            operacao = dadosJSON["operacao"]
            status = dadosJSON["status"]
            
            # Update Estado do Usuario quanto ao login
            if operacao == "login" and status == 200:   
                Usuario.Logado = True                   
            elif operacao == "logoff" and status == 200:
                Usuario.Logado = False
            
            # Montagem da resposta ao usuário
            resposta = ""                   # string vazia, construída com status e operação
            
            if status == 200:               # Se o status da resposta for ok, set azul, negrito e sublinhado para a resposta
                resposta += self.cor.tazul() + self.cor.tnegrito() + self.cor.tsublinhado()
            else:                           # Caso status = 400 ou outra coisa, set vermelho, negrito e sublinhado p/ resposta
                resposta += self.cor.tvermelho() + self.cor.tnegrito() + self.cor.tsublinhado()
            
            if operacao != "get_lista":                     # Se operação não for get_lista, então 
                mensagem = dadosJSON["mensagem"]            # pega a mensagem
                resposta += mensagem + self.cor.end()       # e imprima abaixo
                print(self.cor.tverde() + "Operação: " + self.cor.end() + operacao + '\n' + 
                    self.cor.tverde() + "Status: " + self.cor.end() + str(status) + '\n'+ 
                    self.cor.tverde() + "Mensagem: " + self.cor.end() + resposta)
            else:                                           # Se for get_lista, então
                clientes = dadosJSON["clientes"]            # pega os clientes 
                self.usuariosOnline = clientes              # atualiza  o HashMap (dicionario) de usuariosOnline 
                print(self.cor.tverde() + self.cor.tsublinhado() + "Usuários online: "+ self.cor.end()) # imprime cada cliente
                for cliente in clientes:
                    print('\t' + self.cor.tciano() + '@' + cliente + self.cor.end())
        
        except: # Caso algum erro (exception) ocorra, então o servidor de algum grupo está enviando respostas errado
            print(self.cor.tvermelho() + self.cor.tnegrito() + "Erro nos dados recebidos do servidor" + self.cor.end())
            print(self.cor.tazul() + self.cor.tsublinhado() + "Dados recebidos:" + self.cor.end() + '\n' + dados) # print a resposta recebida como string
            print("\nComo mais nada funcionará na aplicação. Ela será encerrada...")
            sys.exit(1) # Parâmetro 1 no exit para indicar que o encerramento não foi correto
            
                    
    # ---------------------------------- Funcionalidade 2. Interface com usuário final ---------------------------------- #   
    
     # Método (start) que inicia a aplicação (interface com usuário) #
    def start(self):
        print(self.cor.tazul() + self.cor.tnegrito() + self.cor.tsublinhado() + " Bem vindo ao Chat Distribuído !" + self.cor.end() )
        
        self.definirUsername('') # chama com parâmetro vazio, pois nenhum username é dado na linha de comando, assim que inicia o programa
        self.conectarServCentral()
        
        print("Digite " + self.cor.tazul() + "@menu" + self.cor.end() + " para saber os comandos")
        
        self.aguardaConexoes_p2p()                 # Coloca o sockPassivo em modo de escuta para aguardar conexões dos pares (peers)
        self.entradas.append(self.sockPassivo_p2p) # Inclui o sockPassivo do peer na lista de entradas selecionadas enquanto aguarda I/O
        
        while True:
            leitura, escrita, excecao = select.select(self.entradas, [], [])
            for entrada in leitura:
                if entrada == self.sockPassivo_p2p:
                    novoSock_p2p, endereco = self.aceitarConexoes_p2p()
                    peerThread = threading.Thread(target = self.receberMensagem_p2p, args = (novoSock_p2p, endereco))
                    peerThread.start()
                    Usuario.threads_p2p.append(peerThread) # Acrescenta a thread do peer na lista de threads p2p do sistema
                elif entrada == sys.stdin:
                    comando = input()
                    if comando == "@menu":
                        print(self.cor.tazul() + self.cor.tnegrito() + self.cor.tsublinhado() + "MENU DE COMANDOS\n" + self.cor.end() + self.exibirMenu())
                    elif comando == "": # Esse comando vazio é para prevenir um erro quanto ao split
                        pass                    
                    elif comando.split()[0] == "@nick":
                        self.definirUsername(comando)
                    elif comando == "@exit":
                        self.quit()
                        sys.exit(0) # Parâmetro 0 no exit para indicar que o encerramento foi correto
                    elif comando == "@login":
                        self.requisitarLogin()
                    elif comando == "@logoff":
                        self.requisitarLogoff()
                        if Usuario.peersConectados: self.quitAll_p2p()   # Se houver peersConectados assim que faz logoff, fecha tudo
                    elif comando == "@get_lista":
                        self.requisitarLista()
                    elif comando == "@conectados":
                        self.conectados()
                    elif comando.split()[0] == "@info":
                        if self.info(comando) < 0: continue
                    elif comando[0] == "@" and comando.find(":") > 0:
                        if self.conectar_p2p(comando) < 0: continue
                    else:
                        print(self.cor.tnegrito() + self.cor.tvermelho() + "COMANDO DE ENTRADA INVÁLIDO !" + self.cor.end())
    
    # Imprime o Menu de comandos #
    def exibirMenu(self):
        return(self.cor.tsublinhado() + "Comandos aceitos:\n" + self.cor.end() + 
            self.cor.tazul() + " 1. @menu: " + self.cor.end() + "Exibe o menu de comandos.\n"+
            self.cor.tazul() + " 2. @nick <Nickname>: " + self.cor.end() + "Define um Nickname para entrar online. \n" + 
            "\t(!) Se não for passado <Nickname>, chama um input\n" +
            self.cor.tazul() + " 3. @exit: " + self.cor.end() + "Encerra aplicação.\n\t(!) Se houver conexões (com ServidorCentral ou P2P) encerra.\n"+
            self.cor.tazul() + " 4. @login: " + self.cor.end() + "Faz requisição de login sob o Nickname de entrada da aplicação.\n"+
            self.cor.tazul() + " 5. @logoff: " + self.cor.end() + " Faz logoff no Nickname, permitindo o usuario escolher outro.\n"+
            self.cor.tazul() + " 6. @get_lista: " + self.cor.end() + "Requisita e recebe a lista de usuários online.\n"+
            self.cor.tazul() + " 7. @conectados: " + self.cor.end() + "Imprime informação dos peers conectados ao chat. \n"+
            self.cor.tazul() + " 8. @info <Username>: " + self.cor.end() + "Imprime info de um usuario especifico online.\n " +
            "\t(!) Se não for passado <Username> imprime do próprio <Nickname>.\n\n" + 
            self.cor.tsublinhado() + "Para enviar mensagem: \n" + self.cor.end() +  self.cor.tazul() + 
            "\t@get_lista" + self.cor.end() + ": Para atualizar a lista e ter os peers online" + self.cor.tazul() +
            "\n\t@peer : MSG" + self.cor.end() + ", onde peer é o usuário destinatário da mensagem e os dois pontos separa o peername da MSG")
        
    # Permite o usuário setar seu (novo) username (nickname) #
    # // Entrada: Comando digitado na interface
    def definirUsername(self, comando):
        if Usuario.Logado:                                   # Se o usuario está online, faça logoff antes de setar outro nickname
            print("Logoff sob o antigo username sendo efetuado primeiro...")
            self.requisitarLogoff()
            if Usuario.peersConectados: self.quitAll_p2p()   # Se houver peersConectados assim que faz logoff, então fecha tudo, sem encerrar o programa
            if Usuario.Logado:                               # Se o usuario continua logado então deu erro logoff
                print(self.cor.tvermelho() + self.cor.tnegrito() + "Erro no Logoff enquanto tentava-se trocar de nickname" + self.cor.end())
                return                                       # retorna pro menu
        
        if comando == '':                                    # Se comando for vazio, então nenhum username foi passado na linha de comando
            self.username = input("Entre com um username no chat: ") # dê input
            return                                                   # volte ao menu
   
        self.username = comando[6:]    # username passado na linha de comando, onde o 6 indica o começo do username digitado pós @nick
             
        print(self.cor.tazul() + self.cor.tnegrito() + self.cor.tsublinhado() + "Username definido!" + self.cor.end())
        print("Bem vindo, @" + self.cor.tazul() + self.cor.tnegrito() + self.cor.tsublinhado() + self.username + self.cor.end())
        print("Faça " + self.cor.tazul()  +  "@login" + self.cor.end() + " para se registrar no Servidor Central")
                    
    # Método que imprime as informações de um usuário específico online. Caso não seja informado tal usuário, 
    # imprime as informação de conexão do USERNAME do usuário final no Servidor Central #
    # // Entrada: Comando digitado na interface
    # // Saída: Um booleano 1 ou -1 em caso de sucesso ou insucesso
    def info(self, comando):
        try:
            username = comando.split()[1]
            info = self.usuariosOnline.get(username)
            if info:
                print(self.cor.tazul() + self.cor.tsublinhado() + self.cor.tnegrito() + "Informações de: " + self.cor.end() + '@' + username)
                print(self.cor.tazul() + "Endereco: "  + self.cor.end() + info["Endereco"] + '\n' + 
                      self.cor.tazul() + "Porta: " + self.cor.end() + info["Porta"])
                return 1
            else:
                print(self.cor.tnegrito() + self.cor.tvermelho() + "Usuário: " + self.cor.tazul() + '@' + username + self.cor.end() + 
                      self.cor.tvermelho() + " não online. Requisite a lista de usuários, para atualizá-la" + self.cor.end())
                return -1
        except IndexError:
            chatsAbertos = len(Usuario.peersConectados)
            print(self.cor.tazul() + self.cor.tsublinhado() + self.cor.tnegrito() + "Informações suas: " + self.cor.end() + '@' + self.username)
            print(self.cor.tazul() + "Host: "  + self.cor.end() + self.host+ '\n' + 
                  self.cor.tazul() + "Porta: " + self.cor.end() + str(self.porta) + '\n' +
                  self.cor.tazul() + "Chats abertos: " + self.cor.end() + str(chatsAbertos) ) 
            return 1       

    # Método que imprime as informações de todos os peers conectados ao usuario final da aplicação. #
    def conectados(self):
        self.requisitarLista()              # Atualiza a lista para evitar bugs
        print(self.cor.tsublinhado() + self.cor.tazul() + self.cor.tnegrito() + "Usuarios Conectados" + self.cor.end())
        if len(Usuario.peersConectados) == 0:   print(self.cor.tvermelho() + "Nenhum peer conectado" + self.cor.end())
        for peer in Usuario.peersConectados:
            Peer = Usuario.peersConectados.get(peer)
            username = Peer["username"]            
            porta = Peer["porta"]
            corPeer = Peer["cor"]
            print(self.cor.tazul() + "Username: " + self.cor.end() + self.cor.tvermelho() + '@' + self.cor.end() + 
                  corPeer() + username + self.cor.end() + '\n' + 
                  self.cor.tazul() + "Endereço: " +  self.cor.end() + corPeer() + peer + self.cor.end() + '\n' + 
                  self.cor.tazul() + "Porta: " +  self.cor.end() + corPeer() + str(porta) + self.cor.end() )

    # Encerra a aplicação #
    def quit(self):
        print(self.cor.tazul() + self.cor.tnegrito() + self.cor.tsublinhado() + "Programa sendo encerrado..." + self.cor.end())
        
        # Encerra todas as conexões P2P, caso existam
        if Usuario.peersConectados: self.quitAll_p2p()  
        
        # Encerra todas as threads
        for peerThread in Usuario.threads_p2p:   
            peerThread.join()            # aguarda elas terminarem
            print("Thread " + str(peerThread) + " Encerrada")
        
        # zerar a lista de threads, mas o garbage collector do python resolve isso ja que o app ta fechando
        
        # Requisita um logoff no Servidor Central antes de fechar todas as conexões P2P
        if Usuario.Logado == True:  
            self.requisitarLogoff()
            if Usuario.Logado:  # Se o usuário contina logado, deu erro no logoff, mas como a aplicação está encerrado
                pass            # pass tal erro = não faça nada
        
        # Encerra conexão com servidor central
        self.sockServidor.close()        
        
        return

   # ---------------------------------- Funcionalidade 3. Comunicação P2P ----------------------------------- #   

    # Método que aguarda conexões P2P, colocando ele em modo passivo para receber conexões #
    def aguardaConexoes_p2p(self):
        try:
            self.sockPassivo_p2p.bind((self.host, self.porta))
            print(self.cor.tazul() + self.cor.tnegrito() + self.cor.tsublinhado() + "Aplicação aguardando peers..." + self.cor.end())
            self.sockPassivo_p2p.setblocking(False)
            self.sockPassivo_p2p.listen(self.nConexoes)
        except:
            print(self.cor.tvermelho() + self.cor.tnegrito() + "Não foi possível aguardar conexões nessa porta: " + self.cor.end() + str(self.porta))
            self.quit()
            sys.exit(0) # Parâmetro 0 no exit para indicar que o encerramento foi correto
            
    # Método que aceita as conexões do modo de escuta (passivo) #
    def aceitarConexoes_p2p(self):
        peerSock, endereco = self.sockPassivo_p2p.accept()
        print("Conectado com: ", endereco)
        return (peerSock, endereco)

    # Método executado pelas threads para receber e imprimir as mensagens dos peers, na interface do usuário final #
    # // Entrada: peerSock cuja thread executará o receive e o endereco desse peer
    def receberMensagem_p2p(self, peerSock, endereco):
        while True:
            # Recepção dos 2 primeiros bytes
            tamMsgBytes = peerSock.recv(2)                           
            if not tamMsgBytes:                                      # Se não receber, peer encerrou
                self.encerrarConexao_p2p(endereco, peerSock)         # encerra conexão p2p
                # faltou tirar a thread da lista de threads
                return                                               # quebra a função executada pela thread
            
            # Caso receba
            tamMsgInt = int.from_bytes(tamMsgBytes, "big")           # Converte o tamMsg para inteiro BigEndian
            #dados = self.ChunksRecebidosToMsg(tamMsgInt, peerSock)   # recebe chunk by chunk all data 
            
            # Recebimento da mensagem
            dadosBytes = peerSock.recv(tamMsgInt + 1024)
            dados = dadosBytes.decode("utf-8")
            
            # Tente:
            try:             
                dadosDict = json.loads(dados)                        # JSON to Dict (Hashmap)   
                username = dadosDict["username"]
                mensagem = dadosDict["mensagem"]
                enderecoPeer = endereco[0]                           # IP
                porta = endereco[1]                                  # porta
                        
                findPeer = Usuario.peersConectados.get(enderecoPeer) # tenta encontrar uma conexão entre o peer que enviou uma msg e o usuario 
                if not findPeer:                                     # se não existe, registra essa conexão em peersConectados
                    nAleatorioToCor = random.randint(0,7)            # lança uma moeda para tirar um número aleatório
                    corUser = self.cor.selecionaCor(nAleatorioToCor) # seleciona uma cor para esse usuário de acordo com valor dessa moeda
                    # Condição de corrida
                    Usuario.lock.acquire()
                    Usuario.peersConectados[enderecoPeer] = {"username": username, "socket": peerSock, "porta": porta, "cor": corUser }
                    Usuario.lock.release()
                    # Fim da Condição de corrida
                    
                findPeer = Usuario.peersConectados.get(enderecoPeer) # faz dnv: tenta encontrar uma conexão entre o peer que enviou uma msg e o usuario 
                corUsuario = findPeer["cor"]
                print(self.cor.tvermelho() + self.cor.tnegrito() + "@" + self.cor.end() + corUsuario() + username + self.cor.end() + ": " + mensagem)
            
            except: # Encerrar a conexão do peer
                print(self.cor.tvermelho() + self.cor.tnegrito() + "Erro nos dados recebidos do peer" + self.cor.end())
                print(self.cor.tazul() + self.cor.tsublinhado() + "Dados recebidos:" + self.cor.end() + '\n' + dados) # print dados recebidos
                print("\nComo esses peers não podem mais trocar dados, devido ao formato, essa thread e conexão serão encerrados")
                self.encerrarConexao_p2p(endereco, peerSock)         # encerra conexão p2p
                # faltou tirar a thread da lista de threads
                return                                               # encerra a thread

    # Método único para fazer conexões P2P e enviar mensagem # 
    # // Entrada: Comando digitado na interface
    def conectar_p2p(self, comando):
        # Verifica se o usuário não está online
        if not Usuario.Logado:                                       
            print("Fazendo login sob esse username: " + self.cor.tazul() + '@' + self.username + self.cor.end() + " primeiro...")
            self.requisitarLogin()                                   # força ele logar
            if not Usuario.Logado:  
                print(self.cor.tvermelho() + self.cor.tnegrito() + "Erro no login enquanto tentava-se conectar com outro peer" + self.cor.end())
                print(self.cor.tazul() + "Escolha outro username" + self.cor.end())
                return -1                                            # retorna pro menu
            
        # Captura o peername (username de quem deseja-se conectar) e a mensagem da linha de comando (interface)
        try:
            username = comando.split(':')[0][1:]  # coloca numa lista o username e a mensagem. 0-ésimo da lista é o username, [1:] = tira o @
            mensagem = comando[len(username) + 2:] # todo o resto da string - @username + '' é a mensagem, onde '' é o caracter vazio
        except IndexError:
            print(self.cor.tnegrito() + self.cor.tvermelho() + "Informe o <Peername> concatenado com" + self.cor.end() + self.tnegrito()+
                  self.cor.tazul() + ' : ' + self.cor.end() + "<Msg>")
            return -1
        
        # Verifica se a conexão que deseja-se estabelecer é a conexão consigo mesmo
        if username == self.username:                               
            print(self.cor.tnegrito() + self.cor.tvermelho() + "Não é possível se comunicar com si mesmo" + self.cor.end())
            return -1                                               # insucesso na conexão
        
        # Verifica se o peer no qual deseja-se conectar e mandar mensagem está online no Servidor Central
        findUserON = self.usuariosOnline.get(username)              
        if not findUserON:                                          # Se não, então não estabelece conexão
            print(self.cor.tnegrito() + self.cor.tvermelho() + "Usuário: " + self.cor.tazul() + '@' + username + self.cor.end() + 
                      self.cor.tvermelho() + " não online. Requisite a lista de usuários, para atualizá-la" + self.cor.end())
            return -1
        
        # Se o usuário está online, então tente:
        try:
            enderecoPeer = findUserON["Endereco"]
            portaPeer = int(findUserON["Porta"])
            
            findPeer = Usuario.peersConectados.get(enderecoPeer)    # Verifica se já existe conexão estabelecida
            if not findPeer:                                        # Se não, então registre ela em peerConectados
                sockAtivo_p2p = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                sockAtivo_p2p.connect((enderecoPeer, portaPeer))
            
                nAleatorioToCor = random.randint(0,7)                # seleciona um nº aleatorio para decidir uma cor para cada usuario conectado
                corUser = self.cor.selecionaCor(nAleatorioToCor)
                Usuario.peersConectados[enderecoPeer] = {
                    "username": username,
                    "socket": sockAtivo_p2p,
                    "porta": portaPeer,
                    "cor": corUser 
                }
                print("Conectado com @" + corUser() + username + self.cor.end() + ': '+ enderecoPeer)
                
                # Assim que ele registra a conexão ativa na 1º vez, designa-se uma thread para receberMensagem nesse socket 
                peerThread = threading.Thread(target = self.receberMensagem_p2p, args = (sockAtivo_p2p, (enderecoPeer, portaPeer)))
                peerThread.start()
        
        except: # Caso algum erro tenha ocorrido
            infoUser = json.dumps(findUserON)
            print(self.cor.tvermelho() + self.cor.tsublinhado() + "Não foi possível estabelecer uma conexão ativa com: " + self.cor.end() + username)
            print(self.cor.tazul() + self.cor.tsublinhado() + "Informações recebidas desse usuário: " + self.cor.end() + '\n' + infoUser)
            return -1 # volta ao menu
        
        # Envia a mensagem para esse username
        self.enviarMensagem_p2p(enderecoPeer, username, mensagem )    
        return 1
    
    # Método que envia mensagens para os peers, no formato JSON decidido #
    # // Entrada: Strings contendo o Endereco do Peer, Username do Peer e a Mensagem a ser enviada ao Peer
    def enviarMensagem_p2p(self, endereco, username, mensagem):
        socket = Usuario.peersConectados.get(endereco)["socket"]    # sempre encontra um peer conectado pois só é chamado ao final de conectar_p2p
        msgToPeer = {
            "username" : self.username,
            "mensagem" : mensagem
        }
        msgToPeerString = json.dumps(msgToPeer)
        msgToPeerBytes = self.msgToBytes(msgToPeerString)
        socket.sendall(msgToPeerBytes)
                
    def encerrarConexao_p2p(self, endereco, peerSock):
        enderecoPeer = endereco[0]
        findPeer = Usuario.peersConectados.get(enderecoPeer)
        if findPeer:
            username = findPeer["username"]
            corUsuario = findPeer["cor"]
            print(self.cor.tazul() + self.cor.tsublinhado() + "Encerrando conexão com peer: " + self.cor.end() + corUsuario() + '@' + username + self.cor.end())
            socketPeer = findPeer["socket"].close()   # fecha o socket
            # Condição de corrida
            Usuario.lock.acquire()
            del Usuario.peersConectados[enderecoPeer]
            Usuario.lock.release()
            # Fim da condição de corrida
        else:
            print("Conexão não registrada sendo encerrada")
            peerSock.close()

    # Encerra todas as conexões P2P do Usuario #
    def quitAll_p2p(self):
        print(self.cor.tazul() + "Encerrando todas as conexões..." + self.cor.end())
                       
        # Encerrando todas as conexões com peers 
        for peer in Usuario.peersConectados:
            Peer = Usuario.peersConectados.get(peer)
            print("Encerrando conexão com " + Peer["username"] + " no endereço " + peer + " na porta " + str(Peer["porta"]))
            sockPeer = Usuario.peersConectados[peer].get("socket")
            sockPeer.close()
            
        # Encerra o modo de escuta para evitar de receber novas conexões de peers
        self.sockPassivo_p2p.close()           
                        
        return
            
# ToDo - Tratar erro, caso o HOSTSC,PORTASC sejam invalidos. Bloquear o usuário final de avançar
def main():
    host = input("Digite o seu IP: ")                             # Endereço IP do Usuário Final 
    porta = input("Digite a PORTA para se manter em escuta: ")    # Aceita conexões nessa porta
    nConexoes = 3                                                 # nConexoes aceitas = nº conversas
    
    HOSTSC = input("Digite o HOST do Servidor Central: ") 
    PORTASC = input("Digite a PORTA do Servidor Central: ")       # Conecta-se no Servidor Central na porta dele 
    
    app = Usuario(host, int(porta), nConexoes, HOSTSC, int(PORTASC))
    app.start()
    
    
if __name__ == "__main__":
    main()
