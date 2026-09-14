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
    R               -> ver o ranking dos jogadores (no fim de jogo)
    N               -> jogar de novo (no fim de jogo)
    Q               -> sair

O ranking fica salvo no arquivo texto ranking.txt, ao lado deste programa.
"""

import curses
import os
import random
import time

# ---------------------------------------------------------------------------
# 1. CONSTANTES
# ---------------------------------------------------------------------------

LARGURA = 10   # número de colunas do tabuleiro
ALTURA = 18    # número de linhas do tabuleiro (18 em vez de 20 para caber em terminais menores)

INTERVALO_QUEDA = 0.5   # segundos entre cada queda automática da peça
POLL_MS = 50             # tempo (ms) que o curses espera por uma tecla

# Usado nas telas que devem PARAR e esperar o jogador (nome, ranking, aviso de
# terminal pequeno). Cuidado: nodelay(False) NÃO serve aqui - no PDCurses, que
# é o curses do Windows, ele limpa só a flag interna e deixa o tempo de espera
# anterior valendo, então o getch() voltava sozinho depois de POLL_MS e a tela
# piscava e sumia. timeout(-1) zera as duas coisas e bloqueia de verdade.
ESPERA_INFINITA = -1

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

# arquivo texto do ranking, guardado sempre na MESMA pasta do programa (e não
# na pasta de onde o terminal foi aberto, que pode ser outra)
ARQUIVO_RANKING = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "ranking.txt"
)
SEPARADOR_RANKING = ";"   # separa os campos de cada linha do arquivo
TAMANHO_MAX_NOME = 12     # mantém o ranking alinhado em colunas
TOP_RANKING = 10          # quantas partidas aparecem na tela de ranking


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
    def __init__(self, nome="ANONIMO"):
        self.nome = nome
        self.tabuleiro = criar_tabuleiro()
        self.peca_atual = nova_peca()
        self.proxima_peca = nova_peca()   # já sorteada, para mostrar no HUD
        self.pontuacao = 0
        self.game_over = False
        self.ultima_queda = time.time()
        self.inicio = time.time()         # cronômetro da partida
        self.tempo_final = None           # congela o tempo no fim de jogo

    def tempo_decorrido(self):
        """Segundos desde o início da partida (congelados no fim de jogo)."""
        if self.tempo_final is not None:
            return self.tempo_final
        return time.time() - self.inicio

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

        # a peça que estava anunciada no HUD entra em jogo e outra é sorteada
        self.peca_atual = self.proxima_peca
        self.proxima_peca = nova_peca()

        forma = forma_da_peca(self.peca_atual)
        if not posicao_valida(self.tabuleiro, forma, self.peca_atual["linha"], self.peca_atual["coluna"]):
            self.game_over = True
            self.tempo_final = time.time() - self.inicio

    def queda_automatica(self):
        if not self.tentar_mover(1, 0):
            self.travar_peca_atual()

    def queda_instantanea(self):
        while self.tentar_mover(1, 0):
            pass
        self.travar_peca_atual()


# ---------------------------------------------------------------------------
# 5. RANKING (PERSISTÊNCIA EM ARQUIVO TEXTO)
# ---------------------------------------------------------------------------
# Cada partida vira UMA linha do arquivo, com os campos separados por ";":
#     NOME;PONTUACAO;TEMPO_EM_SEGUNDOS;DATA
# Ler e escrever texto simples assim é o suficiente aqui e deixa o arquivo
# legível em qualquer editor - dá para conferir o ranking sem abrir o jogo.


def formatar_tempo(segundos):
    """Converte segundos em MM:SS, que é como o tempo aparece na tela."""
    segundos = int(segundos)
    return "{:02d}:{:02d}".format(segundos // 60, segundos % 60)


def limpar_nome(nome):
    """Deixa o nome seguro para ir ao arquivo.

    Tira o ";" (que é o separador de campos e quebraria a leitura), corta
    espaços das pontas e limita o tamanho para o ranking ficar alinhado.
    """
    nome = nome.replace(SEPARADOR_RANKING, " ").strip()
    return nome[:TAMANHO_MAX_NOME] if nome else "ANONIMO"


def salvar_pontuacao(nome, pontuacao, tempo, caminho=ARQUIVO_RANKING):
    """Acrescenta a partida no fim do arquivo de ranking.

    O modo "a" (append) preserva as partidas anteriores. Se der algum erro de
    disco/permissão, o jogo não pode quebrar por causa disso: devolve False.
    """
    linha = SEPARADOR_RANKING.join([
        limpar_nome(nome),
        str(int(pontuacao)),
        str(int(tempo)),
        time.strftime("%d/%m/%Y %H:%M"),
    ])
    try:
        with open(caminho, "a", encoding="utf-8") as arquivo:
            arquivo.write(linha + "\n")   # uma partida por linha
        return True
    except OSError:
        return False


def carregar_ranking(caminho=ARQUIVO_RANKING):
    """Lê o arquivo e devolve a lista de partidas JÁ ORDENADA.

    Critério de ordenação (o desempate pedido no enunciado):
        1º) maior pontuação primeiro;
        2º) empatou na pontuação? menor tempo primeiro - quem fez os mesmos
            pontos mais rápido fica na frente.

    Isso é feito com uma chave de ordenação composta: a pontuação entra
    negada (-pontuacao) para ficar em ordem decrescente, enquanto o tempo
    entra normal, em ordem crescente.
    """
    partidas = []
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            for linha in arquivo:
                campos = linha.strip().split(SEPARADOR_RANKING)
                if len(campos) < 3:
                    continue  # linha vazia ou incompleta: ignora
                try:
                    pontuacao = int(campos[1])
                    tempo = int(campos[2])
                except ValueError:
                    continue  # linha corrompida (texto onde devia ter número)
                partidas.append({
                    "nome": campos[0],
                    "pontuacao": pontuacao,
                    "tempo": tempo,
                    "data": campos[3] if len(campos) > 3 else "",
                })
    except FileNotFoundError:
        return []   # primeira vez que o jogo roda: ainda não há ranking
    except OSError:
        return []

    partidas.sort(key=lambda partida: (-partida["pontuacao"], partida["tempo"]))
    return partidas


def linhas_do_ranking(partidas):
    """Monta o texto do ranking (lista de linhas) a partir das partidas."""
    if not partidas:
        return ["Ainda nao ha partidas salvas."]

    linhas = ["  #  NOME          PONTOS   TEMPO"]
    for posicao, partida in enumerate(partidas[:TOP_RANKING], start=1):
        linhas.append("{:3d}  {:<12} {:>6}   {}".format(
            posicao,
            partida["nome"],
            partida["pontuacao"],
            formatar_tempo(partida["tempo"]),
        ))
    return linhas


# ---------------------------------------------------------------------------
# 6. DESENHO (RENDERIZAÇÃO)
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


def desenhar_proxima(stdscr, peca, linha_tela, coluna_tela, com_cor):
    """Desenha o quadradinho que anuncia a próxima peça.

    A peça é guardada numa matriz 4x4, mas quase sempre sobra linha/coluna
    vazia em volta. Aqui descobrimos o "retângulo mínimo" que contém as
    células preenchidas e desenhamos só ele, centralizado na moldura - assim
    o I e o O aparecem no meio do quadrado, e não jogados num canto.
    """
    forma = forma_da_peca(peca)
    id_peca = ID_DA_PECA[peca["tipo"]]

    preenchidas = [
        (i, j)
        for i in range(len(forma))
        for j in range(len(forma[i]))
        if forma[i][j] != 0
    ]
    linha_min = min(i for i, _j in preenchidas)
    linha_max = max(i for i, _j in preenchidas)
    coluna_min = min(j for _i, j in preenchidas)
    coluna_max = max(j for _i, j in preenchidas)

    colunas_caixa = 4                                  # sempre 4 células de largura
    linhas_caixa = max(2, linha_max - linha_min + 1)   # altura da maior peça
    largura_texto = colunas_caixa * LARGURA_CELULA

    try:
        stdscr.addstr(linha_tela, coluna_tela, "+" + "-" * largura_texto + "+")
        for indice in range(linhas_caixa):
            stdscr.addstr(linha_tela + 1 + indice, coluna_tela, "|")
            stdscr.addstr(linha_tela + 1 + indice, coluna_tela + 1 + largura_texto, "|")
        stdscr.addstr(linha_tela + 1 + linhas_caixa, coluna_tela,
                      "+" + "-" * largura_texto + "+")
    except curses.error:
        pass

    # deslocamentos para centralizar a peça dentro da moldura
    desloc_linha = (linhas_caixa - (linha_max - linha_min + 1)) // 2
    desloc_coluna = (colunas_caixa - (coluna_max - coluna_min + 1)) // 2

    for i, j in preenchidas:
        desenhar_celula(
            stdscr,
            linha_tela + 1 + desloc_linha + (i - linha_min),
            coluna_tela + 1 + (desloc_coluna + (j - coluna_min)) * LARGURA_CELULA,
            id_peca,
            com_cor,
        )

    return linha_tela + linhas_caixa + 2   # primeira linha livre abaixo da moldura


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
        f"Jogador: {jogo.nome}",
        f"Pontuacao: {jogo.pontuacao}",
        f"Tempo: {formatar_tempo(jogo.tempo_decorrido())}",
        "",
        "Proxima:",
    ]
    for indice, texto in enumerate(linhas_hud):
        try:
            stdscr.addstr(TOPO + indice, coluna_hud, texto)
        except curses.error:
            pass

    # quadradinho com a peça que entra depois da atual
    linha_ajuda = desenhar_proxima(
        stdscr, jogo.proxima_peca, TOPO + len(linhas_hud), coluna_hud, com_cor
    )

    ajuda = [
        "Setas/WASD: mover",
        "Cima/W: rotacionar",
        "Espaco: queda rapida",
        "Q: sair",
    ]
    # R e N só valem depois do fim de jogo, então nem aparecem durante a partida
    if jogo.game_over:
        ajuda.insert(3, "R: ranking")
        ajuda.insert(4, "N: jogar de novo")
    for indice, texto in enumerate(ajuda):
        try:
            stdscr.addstr(linha_ajuda + indice, coluna_hud, texto)
        except curses.error:
            pass

    if jogo.game_over:
        largura_campo = LARGURA * LARGURA_CELULA
        mensagens = [
            " FIM DE JOGO!",
            f" Pontos: {jogo.pontuacao}",
            f" Tempo: {formatar_tempo(jogo.tempo_decorrido())}",
            " R:ranking N:novo",
            " Q: sair",
        ]
        for indice, mensagem in enumerate(mensagens):
            # ljust preenche a linha inteira com espaços: sem isso as peças do
            # tabuleiro continuariam aparecendo no meio do texto
            try:
                stdscr.addstr(
                    TOPO + ALTURA // 2 - 2 + indice,
                    ESQUERDA,
                    mensagem[:largura_campo].ljust(largura_campo),
                )
            except curses.error:
                pass

    stdscr.refresh()


# ---------------------------------------------------------------------------
# 7. LOOP PRINCIPAL
# ---------------------------------------------------------------------------

TECLAS_ESQUERDA = (curses.KEY_LEFT, ord("a"), ord("A"))
TECLAS_DIREITA = (curses.KEY_RIGHT, ord("d"), ord("D"))
TECLAS_BAIXO = (curses.KEY_DOWN, ord("s"), ord("S"))
TECLAS_ROTACIONAR = (curses.KEY_UP, ord("w"), ord("W"))
TECLAS_QUEDA_RAPIDA = (ord(" "),)
TECLAS_RANKING = (ord("r"), ord("R"))
TECLAS_JOGAR_DE_NOVO = (ord("n"), ord("N"))
TECLAS_SAIR = (ord("q"), ord("Q"))
TECLAS_CONFIRMAR = (curses.KEY_ENTER, 10, 13)
TECLAS_APAGAR = (curses.KEY_BACKSPACE, 8, 127)
TECLA_ESC = 27


# TOPO-1 (borda de cima) até TOPO+ALTURA (borda de baixo) = ALTURA + 2 linhas
LINHAS_NECESSARIAS = ALTURA + 2
COLUNAS_NECESSARIAS = ESQUERDA + LARGURA * LARGURA_CELULA + 25


def tamanho_minimo_ok(stdscr):
    linhas_tela, colunas_tela = stdscr.getmaxyx()
    return linhas_tela >= LINHAS_NECESSARIAS and colunas_tela >= COLUNAS_NECESSARIAS


def esperar_terminal_crescer(stdscr):
    """Fica avisando enquanto a janela for pequena demais.

    Retorna True quando o terminal ficou grande o bastante e False se o
    jogador desistiu (Q). Sem o refresh() o aviso nunca aparecia na tela e o
    jogo parecia travado.
    """
    stdscr.timeout(ESPERA_INFINITA)
    while not tamanho_minimo_ok(stdscr):
        linhas_tela, colunas_tela = stdscr.getmaxyx()
        avisos = [
            "Terminal pequeno demais para o jogo.",
            f"Necessario: {LINHAS_NECESSARIAS} linhas x {COLUNAS_NECESSARIAS} colunas",
            f"Atual:      {linhas_tela} linhas x {colunas_tela} colunas",
            "",
            "Aumente a janela e pressione qualquer tecla.",
            "Q sai.",
        ]
        stdscr.erase()
        for indice, texto in enumerate(avisos):
            try:
                stdscr.addstr(indice, 0, texto[: max(0, colunas_tela - 1)])
            except curses.error:
                pass
        stdscr.refresh()
        if stdscr.getch() in TECLAS_SAIR:
            return False
    stdscr.timeout(POLL_MS)
    return True


def escrever_linhas(stdscr, linhas, linha_inicial=1, coluna_inicial=2):
    """Escreve uma lista de textos, um por linha, cortando o que não couber."""
    _linhas_tela, colunas_tela = stdscr.getmaxyx()
    for indice, texto in enumerate(linhas):
        try:
            stdscr.addstr(
                linha_inicial + indice,
                coluna_inicial,
                texto[: max(0, colunas_tela - coluna_inicial - 1)],
            )
        except curses.error:
            pass


def ler_nome(stdscr):
    """Tela inicial: pergunta o nome do jogador.

    Monta o nome tecla a tecla (em vez de usar curses.echo/getstr) para poder
    limitar o tamanho, aceitar backspace e deixar o ESC cancelar o jogo.
    Devolve o nome já limpo, ou None se o jogador desistir.
    """
    stdscr.timeout(ESPERA_INFINITA)
    nome = ""
    while True:
        stdscr.erase()
        escrever_linhas(stdscr, [
            "=== MINI TETRIS ===",
            "",
            "Digite o seu nome e tecle ENTER:",
            "",
            "  > " + nome + "_",
            "",
            f"(ate {TAMANHO_MAX_NOME} letras. ESC cancela e sai do jogo.)",
        ])
        stdscr.refresh()

        tecla = stdscr.getch()
        if tecla in TECLAS_CONFIRMAR:
            if nome.strip():
                return limpar_nome(nome)
        elif tecla in TECLAS_APAGAR:
            nome = nome[:-1]
        elif tecla == TECLA_ESC:
            return None
        elif 32 <= tecla <= 126 and len(nome) < TAMANHO_MAX_NOME:
            nome += chr(tecla)


def mostrar_ranking(stdscr, destaque=None):
    """Mostra o ranking lido do arquivo e espera uma tecla para voltar.

    `destaque` é o nome do jogador da partida recém-terminada, só para ele se
    achar mais fácil na lista.
    """
    stdscr.timeout(ESPERA_INFINITA)
    stdscr.erase()

    linhas = ["=== RANKING DOS JOGADORES ===", ""]
    linhas += linhas_do_ranking(carregar_ranking())
    linhas += ["", "Empate na pontuacao? Ganha o menor tempo."]
    if destaque:
        linhas.append(f"Jogador atual: {destaque}")
    linhas += ["", "Pressione qualquer tecla para voltar."]

    escrever_linhas(stdscr, linhas)
    stdscr.refresh()

    # ignora um eventual -1 (nenhuma tecla) e só sai com uma tecla de verdade
    while stdscr.getch() == -1:
        pass

    stdscr.timeout(POLL_MS)   # devolve o modo não-bloqueante usado no jogo


def jogar_partida(stdscr, nome, com_cor):
    """Joga uma partida inteira, do início até o fim de jogo.

    Devolve True se o jogador pediu para jogar de novo (tecla N) e False se
    pediu para sair (tecla Q) - main() usa esse retorno para decidir se
    chama esta função de novo ou encerra o programa.
    """
    jogo = Jogo(nome)
    pontuacao_salva = False

    while True:
        tecla = stdscr.getch()

        # o ranking só abre com a partida encerrada; durante o jogo o R é
        # ignorado de propósito, para não pausar a partida nem parar o relógio
        if tecla in TECLAS_RANKING and jogo.game_over:
            mostrar_ranking(stdscr, destaque=jogo.nome)
            desenhar(stdscr, jogo, com_cor)
            continue

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

        # grava a partida no arquivo assim que o jogo acaba (só uma vez)
        if jogo.game_over and not pontuacao_salva:
            salvar_pontuacao(jogo.nome, jogo.pontuacao, jogo.tempo_decorrido())
            pontuacao_salva = True

        desenhar(stdscr, jogo, com_cor)

        if tecla in TECLAS_SAIR:
            return False
        if jogo.game_over and tecla in TECLAS_JOGAR_DE_NOVO:
            return True


def main(stdscr):
    curses.curs_set(0)
    stdscr.timeout(POLL_MS)
    com_cor = inicializar_cores()

    if not esperar_terminal_crescer(stdscr):
        return

    nome = ler_nome(stdscr)
    if nome is None:
        return
    stdscr.timeout(POLL_MS)   # ler_nome deixou a entrada bloqueante

    while jogar_partida(stdscr, nome, com_cor):
        pass   # jogador apertou N: joga outra partida com o mesmo nome


if __name__ == "__main__":
    curses.wrapper(main)
