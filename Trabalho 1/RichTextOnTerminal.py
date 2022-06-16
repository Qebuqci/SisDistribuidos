#-*- encoding: utf-8

'''
Classe simples, que implementa caracteres de escape (ANSI), para 
deixar o texto mais rico, impresso no terminal, através de cores 
(em foreground e background - cor de fundo) e formatações, em negrito 
(bold) e sublinhado
'''

class RichTextOnTerminal:
    def __init__(self):
        # Caracter especial de escape ANSI, que precede as formatações
        self.prefixo_ANSI = "\u001b["
        # Caracter especial de escape ANSI, que reseta as formatações
        self.reset_ANSI = "\u001b[0m"
    
    # Método que permite selecionar a cor de um texto dado um número inteiro #
    # // Entrada: Um número inteiro aleatório (random) n - escolhido em Usuario
    # // Saída: O endereço de memória do método que modifica a cor do texto, selecionado por n
    def selecionaCor(self, n):
        if n == 0:
            return self.tverde
        if n == 1:
            return self.tamarelo
        if n == 2:
            return self.tazul
        if n == 3:
            return self.trosa
        if n == 4:
            return self.tvermelho
        if n == 5:
            return self.tpreto
        if n == 6:
            return self.tciano
        if n == 7:
            return self.tbranco
    
    # Formatação de cores em foreground #
    
    # Texto preto
    def tpreto(self):
        return self.prefixo_ANSI + "30m"

    # Texto vermelho
    def tvermelho(self):
        return self.prefixo_ANSI + "31m"
    
    # Texto verde
    def tverde(self):
        return self.prefixo_ANSI + "32m"
   
    # Texto amarelo
    def tamarelo(self):
        return self.prefixo_ANSI + "33m"
    
    # Texto azul
    def tazul(self):
        return self.prefixo_ANSI + "34m"
    
    # Texto rosa
    def trosa(self):
        return self.prefixo_ANSI + "35m"
    
    # Texto ciano
    def tciano(self):
        return self.prefixo_ANSI + "36m"
    
    # Texto branco (cinza)
    def tbranco(self):
        return self.prefixo_ANSI + "31m"
    
    # Formatação de cores em background #
    
    # Fundo preto
    def fpreto(self):
        return self.prefixo_ANSI + "40m"
    
    # Fundo vermelho
    def fvermelho(self):
        return self.prefixo_ANSI + "41m"
    
    # Fundo verde
    def fverde(self):
        return self.prefixo_ANSI + "42m"
    
    # Fundo amarelo
    def famarelo(self):
        return self.prefixo_ANSI + "43m"
    
    # Fundo azul escuro
    def fazul(self):
        return self.prefixo_ANSI + "44m"
    
    # Fundo rosa (magenta)
    def frosa(self):
        return self.prefixo_ANSI + "45m"
    
    # Fundo ciano (azul claro)
    def fciano(self):
        return self.prefixo_ANSI + "46m"
    
    # Fundo branco (cinza)
    def fbranco(self):
        return self.prefixo_ANSI + "47m"
        
    # Formatação de texto
    
    # Texto negrito
    def tnegrito(self):
        return self.prefixo_ANSI + "1m"
    
    # Texto sublinhado
    def tsublinhado(self):
        return self.prefixo_ANSI + "4m"
    
    # Caracter reset (volta a formatação padrão do terminal)
    def end(self):
        return self.reset_ANSI

if __name__ == "__main__":
    texto = RichTextOnTerminal()
    print(texto.tsublinhado() + texto.tnegrito() + texto.tvermelho() + "Teste " + texto.end() + str(texto.corAleatoria))
