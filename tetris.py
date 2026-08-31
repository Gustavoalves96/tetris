"""
Mini Tetris - jogo de terminal usando a biblioteca curses.

Trabalho de Algoritmos e Estruturas de Dados I - o tabuleiro do jogo é
representado exatamente como visto em aula: uma MATRIZ (lista de listas),
acessada por tabuleiro[linha][coluna].

Como rodar (Windows):
    pip install -r requirements.txt
    python tetris.py

Controles:
    Setas ou WASD para mover / rotacionar
    Espaço          -> queda instantânea (hard drop)
    Q               -> sair
"""

import curses
import random
import time

# ---------------------------------------------------------------------------
# 1. CONSTANTES
# ---------------------------------------------------------------------------

LARGURA = 10   # número de colunas do tabuleiro
ALTURA = 18    # número de linhas do tabuleiro (18 em vez de 20 para caber em terminais menores)

INTERVALO_QUEDA = 0.5   # segundos entre cada queda automática da peça
POLL_MS = 50             # tempo (ms) que o curses espera por uma tecla

# posição da borda do tabuleiro na tela do terminal
TOPO = 1
ESQUERDA = 1
LARGURA_CELULA = 2   # cada célula é desenhada com 2 caracteres (fica mais "quadrada" no terminal)

# ---------------------------------------------------------------------------
# 2. PEÇAS (TETROMINÓS)
# ---------------------------------------------------------------------------
# Cada peça é uma lista de "estados de rotação". Cada estado é, por sua vez,
# uma pequena matriz 4x4 de 0s e 1s: outra aplicação direta do conceito de
# matriz (lista de listas) visto em aula, só que representando a forma da peça
# em vez de um tabuleiro.

PECAS = {
    "I": [
        [[0, 0, 0, 0],
         [1, 1, 1, 1],
         [0, 0, 0, 0],
         [0, 0, 0, 0]],
        [[0, 0, 1, 0],
         [0, 0, 1, 0],
         [0, 0, 1, 0],
         [0, 0, 1, 0]],
    ],
    "O": [
        [[0, 0, 0, 0],
         [0, 1, 1, 0],
         [0, 1, 1, 0],
         [0, 0, 0, 0]],
    ],
    "T": [
        [[0, 0, 0, 0],
         [1, 1, 1, 0],
         [0, 1, 0, 0],
         [0, 0, 0, 0]],
        [[0, 1, 0, 0],
         [1, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 0, 0, 0]],
        [[0, 1, 0, 0],
         [1, 1, 1, 0],
         [0, 0, 0, 0],
         [0, 0, 0, 0]],
        [[0, 1, 0, 0],
         [0, 1, 1, 0],
         [0, 1, 0, 0],
         [0, 0, 0, 0]],
    ],
    "S": [
        [[0, 0, 0, 0],
         [0, 1, 1, 0],
         [1, 1, 0, 0],
         [0, 0, 0, 0]],
        [[1, 0, 0, 0],
         [1, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 0, 0, 0]],
    ],
    "Z": [
        [[0, 0, 0, 0],
         [1, 1, 0, 0],
         [0, 1, 1, 0],
         [0, 0, 0, 0]],
        [[0, 1, 0, 0],
         [1, 1, 0, 0],
         [1, 0, 0, 0],
         [0, 0, 0, 0]],
    ],
    "J": [
        [[0, 0, 0, 0],
         [1, 0, 0, 0],
         [1, 1, 1, 0],
         [0, 0, 0, 0]],
        [[0, 1, 1, 0],
         [0, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 0, 0, 0]],
        [[0, 0, 0, 0],
         [1, 1, 1, 0],
         [0, 0, 1, 0],
         [0, 0, 0, 0]],
        [[0, 1, 0, 0],
         [0, 1, 0, 0],
         [1, 1, 0, 0],
         [0, 0, 0, 0]],
    ],
    "L": [
        [[0, 0, 0, 0],
         [0, 0, 1, 0],
         [1, 1, 1, 0],
         [0, 0, 0, 0]],
        [[0, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 1, 1, 0],
         [0, 0, 0, 0]],
        [[0, 0, 0, 0],
         [1, 1, 1, 0],
         [1, 0, 0, 0],
         [0, 0, 0, 0]],
        [[1, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 0, 0, 0]],
    ],
}

# ordem fixa das peças -> id numérico (1 a 7), usado tanto para marcar a
# célula ocupada no tabuleiro quanto para escolher a cor
ORDEM_PECAS = ["I", "O", "T", "S", "Z", "J", "L"]
ID_DA_PECA = {tipo: indice + 1 for indice, tipo in enumerate(ORDEM_PECAS)}

PONTOS_POR_LINHAS = {1: 100, 2: 300, 3: 500, 4: 800}


# ---------------------------------------------------------------------------
# 3. FUNÇÕES DO TABULEIRO (MATRIZ)
# ---------------------------------------------------------------------------

def criar_tabuleiro():
    """Cria a matriz do tabuleiro: uma lista de ALTURA listas de LARGURA zeros.

    IMPORTANTE: usamos uma list comprehension para cada linha (e não
    `[[0] * LARGURA] * ALTURA`), porque essa segunda forma criaria ALTURA
    referências para a MESMA lista interna. Nesse caso, alterar uma célula de
    uma "linha" alteraria todas as outras linhas ao mesmo tempo (aliasing) -
    um erro clássico ao trabalhar com matrizes em Python.
    """
    return [[0 for _coluna in range(LARGURA)] for _linha in range(ALTURA)]


def forma_da_peca(peca):
    """Retorna a matriz 4x4 (0/1) correspondente ao estado atual da peça."""
    estados = PECAS[peca["tipo"]]
    return estados[peca["rotacao"] % len(estados)]


def posicao_valida(tabuleiro, forma, linha, coluna):
    """Verifica se a peça (matriz `forma`) cabe no tabuleiro na posição dada.

    Percorre a matriz da peça linha a linha, coluna a coluna. Para cada
    célula preenchida da peça, calcula a posição correspondente no tabuleiro
    e confere se ela está dentro dos limites e livre.
    """
    for i in range(len(forma)):
        for j in range(len(forma[i])):
            if forma[i][j] == 0:
                continue  # célula vazia da peça, não precisa checar

            linha_tab = linha + i
            coluna_tab = coluna + j

            if coluna_tab < 0 or coluna_tab >= LARGURA:
                return False
            if linha_tab >= ALTURA:
                return False
            if linha_tab < 0:
                # parte da peça ainda acima do tabuleiro visível (só ocorre
                # perto do spawn) - não há célula de tabuleiro para checar
                continue
            if tabuleiro[linha_tab][coluna_tab] != 0:
                return False
    return True


def fixar_peca(tabuleiro, peca):
    """Copia as células da peça para a matriz do tabuleiro (peça "assentou")."""
    forma = forma_da_peca(peca)
    id_peca = ID_DA_PECA[peca["tipo"]]
    for i in range(len(forma)):
        for j in range(len(forma[i])):
            if forma[i][j] == 0:
                continue
            linha_tab = peca["linha"] + i
            coluna_tab = peca["coluna"] + j
            if 0 <= linha_tab < ALTURA and 0 <= coluna_tab < LARGURA:
                tabuleiro[linha_tab][coluna_tab] = id_peca


def limpar_linhas(tabuleiro):
    """Remove linhas completas do tabuleiro e insere linhas vazias no topo.

    Retorna o novo tabuleiro e a quantidade de linhas removidas.
    """
    linhas_completas = [
        linha for linha in range(ALTURA)
        if all(celula != 0 for celula in tabuleiro[linha])
    ]

    if not linhas_completas:
        return tabuleiro, 0

    linhas_restantes = [
        tabuleiro[linha] for linha in range(ALTURA) if linha not in linhas_completas
    ]
    linhas_novas = [[0 for _coluna in range(LARGURA)] for _ in linhas_completas]

    novo_tabuleiro = linhas_novas + linhas_restantes
    return novo_tabuleiro, len(linhas_completas)


# ---------------------------------------------------------------------------
# 4. ESTADO DO JOGO / PEÇAS EM QUEDA
# ---------------------------------------------------------------------------

def nova_peca(tipo=None):
    """Cria uma peça nova, posicionada no topo, centralizada no tabuleiro."""
    if tipo is None:
        tipo = random.choice(ORDEM_PECAS)
    return {
        "tipo": tipo,
        "rotacao": 0,
        "linha": 0,
        "coluna": (LARGURA - 4) // 2,
    }


class Jogo:
    def __init__(self):
        self.tabuleiro = criar_tabuleiro()
        self.peca_atual = nova_peca()
        self.pontuacao = 0
        self.game_over = False
        self.ultima_queda = time.time()

    def tentar_mover(self, delta_linha, delta_coluna):
        nova_linha = self.peca_atual["linha"] + delta_linha
        nova_coluna = self.peca_atual["coluna"] + delta_coluna
        forma = forma_da_peca(self.peca_atual)
        if posicao_valida(self.tabuleiro, forma, nova_linha, nova_coluna):
            self.peca_atual["linha"] = nova_linha
            self.peca_atual["coluna"] = nova_coluna
            return True
        return False

    def tentar_rotacionar(self):
        estados = PECAS[self.peca_atual["tipo"]]
        nova_rotacao = (self.peca_atual["rotacao"] + 1) % len(estados)
        forma = estados[nova_rotacao]

        # tenta rotacionar no lugar; se não couber, tenta um pequeno
        # deslocamento para os lados (um "empurrão" simples, sem a
        # complexidade de um sistema completo de wall-kick)
        for deslocamento in (0, -1, 1):
            coluna = self.peca_atual["coluna"] + deslocamento
            if posicao_valida(self.tabuleiro, forma, self.peca_atual["linha"], coluna):
                self.peca_atual["rotacao"] = nova_rotacao
                self.peca_atual["coluna"] = coluna
                return True
        return False

    def travar_peca_atual(self):
        fixar_peca(self.tabuleiro, self.peca_atual)
        self.tabuleiro, linhas_removidas = limpar_linhas(self.tabuleiro)
        if linhas_removidas:
            self.pontuacao += PONTOS_POR_LINHAS.get(linhas_removidas, linhas_removidas * 100)

        self.peca_atual = nova_peca()
        forma = forma_da_peca(self.peca_atual)
        if not posicao_valida(self.tabuleiro, forma, self.peca_atual["linha"], self.peca_atual["coluna"]):
            self.game_over = True

    def queda_automatica(self):
        if not self.tentar_mover(1, 0):
            self.travar_peca_atual()

    def queda_instantanea(self):
        while self.tentar_mover(1, 0):
            pass
        self.travar_peca_atual()


# ---------------------------------------------------------------------------
# 5. DESENHO (RENDERIZAÇÃO)
# ---------------------------------------------------------------------------

def inicializar_cores():
    if not curses.has_colors():
        return False
    curses.start_color()
    cores = [
        curses.COLOR_CYAN, curses.COLOR_YELLOW, curses.COLOR_MAGENTA,
        curses.COLOR_GREEN, curses.COLOR_RED, curses.COLOR_BLUE, curses.COLOR_WHITE,
    ]
    for indice, cor in enumerate(cores, start=1):
        curses.init_pair(indice, curses.COLOR_BLACK, cor)
    return True


def desenhar_celula(stdscr, linha_tela, coluna_tela, id_peca, com_cor):
    texto = "[]" if id_peca else "  "
    atributo = curses.color_pair(id_peca) if com_cor and id_peca else curses.A_NORMAL
    try:
        stdscr.addstr(linha_tela, coluna_tela, texto, atributo)
    except curses.error:
        pass  # terminal pequeno demais para essa posição; ignora e segue


def desenhar_borda(stdscr):
    largura_campo = LARGURA * LARGURA_CELULA
    try:
        stdscr.addstr(TOPO - 1, ESQUERDA - 1, "+" + "-" * largura_campo + "+")
        for linha in range(ALTURA):
            stdscr.addstr(TOPO + linha, ESQUERDA - 1, "|")
            stdscr.addstr(TOPO + linha, ESQUERDA + largura_campo, "|")
        stdscr.addstr(TOPO + ALTURA, ESQUERDA - 1, "+" + "-" * largura_campo + "+")
    except curses.error:
        pass


def desenhar(stdscr, jogo, com_cor):
    stdscr.erase()
    desenhar_borda(stdscr)

    # desenha as peças já assentadas (percorrendo a matriz do tabuleiro)
    for linha in range(ALTURA):
        for coluna in range(LARGURA):
            id_peca = jogo.tabuleiro[linha][coluna]
            desenhar_celula(
                stdscr,
                TOPO + linha,
                ESQUERDA + coluna * LARGURA_CELULA,
                id_peca,
                com_cor,
            )

    # sobrepõe a peça que está caindo (não faz parte da matriz do tabuleiro)
    forma = forma_da_peca(jogo.peca_atual)
    id_peca = ID_DA_PECA[jogo.peca_atual["tipo"]]
    for i in range(len(forma)):
        for j in range(len(forma[i])):
            if forma[i][j] == 0:
                continue
            linha = jogo.peca_atual["linha"] + i
            coluna = jogo.peca_atual["coluna"] + j
            if 0 <= linha < ALTURA and 0 <= coluna < LARGURA:
                desenhar_celula(
                    stdscr,
                    TOPO + linha,
                    ESQUERDA + coluna * LARGURA_CELULA,
                    id_peca,
                    com_cor,
                )

    # painel de informações (HUD) à direita do tabuleiro
    coluna_hud = ESQUERDA + LARGURA * LARGURA_CELULA + 3
    linhas_hud = [
        "MINI TETRIS",
        "",
        f"Pontuacao: {jogo.pontuacao}",
        "",
        "Setas/WASD: mover",
        "Cima/W: rotacionar",
        "Espaco: queda rapida",
        "Q: sair",
    ]
    for indice, texto in enumerate(linhas_hud):
        try:
            stdscr.addstr(TOPO + indice, coluna_hud, texto)
        except curses.error:
            pass

    if jogo.game_over:
        mensagem = f" FIM DE JOGO - Pontuacao: {jogo.pontuacao} - pressione uma tecla "
        try:
            stdscr.addstr(TOPO + ALTURA // 2, ESQUERDA, mensagem[: LARGURA * LARGURA_CELULA])
        except curses.error:
            pass

    stdscr.refresh()


# ---------------------------------------------------------------------------
# 6. LOOP PRINCIPAL
# ---------------------------------------------------------------------------

TECLAS_ESQUERDA = (curses.KEY_LEFT, ord("a"), ord("A"))
TECLAS_DIREITA = (curses.KEY_RIGHT, ord("d"), ord("D"))
TECLAS_BAIXO = (curses.KEY_DOWN, ord("s"), ord("S"))
TECLAS_ROTACIONAR = (curses.KEY_UP, ord("w"), ord("W"))
TECLAS_QUEDA_RAPIDA = (ord(" "),)
TECLAS_SAIR = (ord("q"), ord("Q"))


def tamanho_minimo_ok(stdscr):
    linhas_tela, colunas_tela = stdscr.getmaxyx()
    # TOPO-1 (borda de cima) até TOPO+ALTURA (borda de baixo) = ALTURA + 2 linhas
    linhas_necessarias = ALTURA + 2
    colunas_necessarias = ESQUERDA + LARGURA * LARGURA_CELULA + 25
    return linhas_tela >= linhas_necessarias and colunas_tela >= colunas_necessarias


def main(stdscr):
    curses.curs_set(0)
    stdscr.timeout(POLL_MS)
    com_cor = inicializar_cores()

    if not tamanho_minimo_ok(stdscr):
        stdscr.nodelay(False)
        try:
            stdscr.addstr(0, 0, "Aumente o tamanho do terminal e pressione qualquer tecla.")
        except curses.error:
            pass
        stdscr.getch()
        return

    jogo = Jogo()

    while True:
        tecla = stdscr.getch()

        if not jogo.game_over:
            if tecla in TECLAS_ESQUERDA:
                jogo.tentar_mover(0, -1)
            elif tecla in TECLAS_DIREITA:
                jogo.tentar_mover(0, 1)
            elif tecla in TECLAS_BAIXO:
                jogo.tentar_mover(1, 0)
            elif tecla in TECLAS_ROTACIONAR:
                jogo.tentar_rotacionar()
            elif tecla in TECLAS_QUEDA_RAPIDA:
                jogo.queda_instantanea()

            agora = time.time()
            if agora - jogo.ultima_queda >= INTERVALO_QUEDA:
                jogo.queda_automatica()
                jogo.ultima_queda = agora

        desenhar(stdscr, jogo, com_cor)

        if tecla in TECLAS_SAIR:
            break
        if jogo.game_over and tecla != -1:
            break


if __name__ == "__main__":
    curses.wrapper(main)
