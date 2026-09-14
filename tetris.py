import curses
import os
import random
import time

# ---------------------------------------------------------------------------
# 1. CONSTANTES
# ---------------------------------------------------------------------------

LARGURA = 10
ALTURA = 18

INTERVALO_QUEDA = 0.5
POLL_MS = 50

ESPERA_INFINITA = -1

TOPO = 1
ESQUERDA = 1
LARGURA_CELULA = 2

# ---------------------------------------------------------------------------
# 2. PEÇAS (TETROMINÓS)
# ---------------------------------------------------------------------------

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

ORDEM_PECAS = ["I", "O", "T", "S", "Z", "J", "L"]
ID_DA_PECA = {tipo: indice + 1 for indice, tipo in enumerate(ORDEM_PECAS)}

PONTOS_POR_LINHAS = {1: 100, 2: 300, 3: 500, 4: 800}

ARQUIVO_RANKING = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "ranking.txt"
)
SEPARADOR_RANKING = ";"
TAMANHO_MAX_NOME = 12
TOP_RANKING = 10


# ---------------------------------------------------------------------------
# 3. FUNÇÕES DO TABULEIRO (MATRIZ)
# ---------------------------------------------------------------------------

def criar_tabuleiro():
    return [[0 for _coluna in range(LARGURA)] for _linha in range(ALTURA)]


def forma_da_peca(peca):
    estados = PECAS[peca["tipo"]]
    return estados[peca["rotacao"] % len(estados)]


def posicao_valida(tabuleiro, forma, linha, coluna):
    for i in range(len(forma)):
        for j in range(len(forma[i])):
            if forma[i][j] == 0:
                continue

            linha_tab = linha + i
            coluna_tab = coluna + j

            if coluna_tab < 0 or coluna_tab >= LARGURA:
                return False
            if linha_tab >= ALTURA:
                return False
            if linha_tab < 0:
                continue
            if tabuleiro[linha_tab][coluna_tab] != 0:
                return False
    return True


def fixar_peca(tabuleiro, peca):
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
        self.proxima_peca = nova_peca()
        self.pontuacao = 0
        self.game_over = False
        self.ultima_queda = time.time()
        self.inicio = time.time()
        self.tempo_final = None

    def tempo_decorrido(self):
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


def formatar_tempo(segundos):
    segundos = int(segundos)
    return "{:02d}:{:02d}".format(segundos // 60, segundos % 60)


def limpar_nome(nome):
    nome = nome.replace(SEPARADOR_RANKING, " ").strip()
    return nome[:TAMANHO_MAX_NOME] if nome else "ANONIMO"


def salvar_pontuacao(nome, pontuacao, tempo, caminho=ARQUIVO_RANKING):
    linha = SEPARADOR_RANKING.join([
        limpar_nome(nome),
        str(int(pontuacao)),
        str(int(tempo)),
        time.strftime("%d/%m/%Y %H:%M"),
    ])
    try:
        with open(caminho, "a", encoding="utf-8") as arquivo:
            arquivo.write(linha + "\n")
        return True
    except OSError:
        return False


def carregar_ranking(caminho=ARQUIVO_RANKING):
    partidas = []
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            for linha in arquivo:
                campos = linha.strip().split(SEPARADOR_RANKING)
                if len(campos) < 3:
                    continue
                try:
                    pontuacao = int(campos[1])
                    tempo = int(campos[2])
                except ValueError:
                    continue
                partidas.append({
                    "nome": campos[0],
                    "pontuacao": pontuacao,
                    "tempo": tempo,
                    "data": campos[3] if len(campos) > 3 else "",
                })
    except FileNotFoundError:
        return []
    except OSError:
        return []

    partidas.sort(key=lambda partida: (-partida["pontuacao"], partida["tempo"]))
    return partidas


def linhas_do_ranking(partidas):
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
        pass


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

    colunas_caixa = 4
    linhas_caixa = max(2, linha_max - linha_min + 1)
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

    return linha_tela + linhas_caixa + 2


def desenhar(stdscr, jogo, com_cor):
    stdscr.erase()
    desenhar_borda(stdscr)

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

    linha_ajuda = desenhar_proxima(
        stdscr, jogo.proxima_peca, TOPO + len(linhas_hud), coluna_hud, com_cor
    )

    ajuda = [
        "Setas/WASD: mover",
        "Cima/W: rotacionar",
        "Espaco: queda rapida",
        "Q: sair",
    ]
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


LINHAS_NECESSARIAS = ALTURA + 2
COLUNAS_NECESSARIAS = ESQUERDA + LARGURA * LARGURA_CELULA + 25


def tamanho_minimo_ok(stdscr):
    linhas_tela, colunas_tela = stdscr.getmaxyx()
    return linhas_tela >= LINHAS_NECESSARIAS and colunas_tela >= COLUNAS_NECESSARIAS


def esperar_terminal_crescer(stdscr):
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

    while stdscr.getch() == -1:
        pass

    stdscr.timeout(POLL_MS)


def jogar_partida(stdscr, nome, com_cor):
    jogo = Jogo(nome)
    pontuacao_salva = False

    while True:
        tecla = stdscr.getch()

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
    stdscr.timeout(POLL_MS)

    while jogar_partida(stdscr, nome, com_cor):
        pass


if __name__ == "__main__":
    curses.wrapper(main)
