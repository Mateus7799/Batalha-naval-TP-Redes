import socket
import threading

HOST = '0.0.0.0'
PORT = 5555

TABULEIRO = 5        # Dimensão do tabuleiro (5x5)
QUANTIDADE_BARCOS = 3  # Barcos por jogador

# ============================================================
# ESTADO GLOBAL DO JOGO
# Protegido por 'lock' para evitar condições de corrida
# entre as threads dos dois jogadores.
# ============================================================
lock = threading.Lock()

jogadores = []   # Sockets dos clientes
nomes = []       # Nomes dos jogadores
tabuleiros = []  # Tabuleiros (lista de listas)
turno = 0        # Índice do jogador que deve atacar agora
fim_jogo = False # Flag para encerrar o loop de jogo

# Barrier garante que as 2 threads só avançam para o jogo
# depois que AMBOS os tabuleiros foram totalmente preenchidos.
barreira = threading.Barrier(2)

def criar_tabuleiro():
    """Retorna um tabuleiro 5x5 preenchido com '~' (água)."""
    return [['~' for _ in range(TABULEIRO)] for _ in range(TABULEIRO)]


def enviar(cliente, mensagem):
    """Envia uma mensagem com quebra de linha para o cliente."""
    try:
        cliente.sendall((mensagem + '\n').encode())
    except OSError:
        pass  # Ignora se o cliente já desconectou


def tabuleiro_texto(tabuleiro, ocultar=False):
    """
    Formata o tabuleiro como string para exibição no console.

    Parâmetros:
        tabuleiro: lista 2D com o estado do tabuleiro
        ocultar:   se True, esconde os barcos inimigos ('B' → '~')

    Legenda:
        ~  → água (não atacada)
        B  → barco próprio (visível apenas no tabuleiro do dono)
        X  → barco acertado
        O  → água atacada (erro)
    """
    # Cabeçalho dinâmico de colunas
    header = '  ' + ' '.join(str(c) for c in range(TABULEIRO))
    texto = header + '\n'

    for i, linha in enumerate(tabuleiro):
        texto += str(i) + ' '
        for item in linha:
            if ocultar and item == 'B':
                texto += '~ '
            else:
                texto += item + ' '
        texto += '\n'

    return texto.rstrip('\n')


def barcos_restantes(tabuleiro):
    """Retorna True se ainda há algum barco ('B') no tabuleiro."""
    return any('B' in linha for linha in tabuleiro)


def separador(cliente):
    """Envia uma linha separadora para melhorar a legibilidade."""
    enviar(cliente, '-' * 30)


def posicionar_barcos(cliente, tabuleiro):
    """
    Solicita ao jogador as coordenadas para posicionar seus barcos.
    Valida entrada, posição inválida e sobreposição.
    """
    enviar(cliente, '=== POSICIONAMENTO DOS BARCOS ===')
    enviar(cliente, f'Você deve posicionar {QUANTIDADE_BARCOS} barcos.')
    enviar(cliente, 'Formato: linha coluna  (ex: 2 3)')

    barcos_colocados = 0

    while barcos_colocados < QUANTIDADE_BARCOS:
        enviar(cliente, tabuleiro_texto(tabuleiro))
        enviar(cliente, f'[{barcos_colocados + 1}/{QUANTIDADE_BARCOS}] Coordenadas do barco:')

        try:
            dados = cliente.recv(1024).decode().strip()

            partes = dados.split()
            if len(partes) != 2:
                enviar(cliente, 'ERRO: Digite exatamente dois números (linha coluna).')
                continue

            x, y = int(partes[0]), int(partes[1])

            if not (0 <= x < TABULEIRO and 0 <= y < TABULEIRO):
                enviar(cliente, f'ERRO: Posição fora do tabuleiro! Use valores entre 0 e {TABULEIRO - 1}.')
                continue

            if tabuleiro[x][y] == 'B':
                enviar(cliente, 'ERRO: Já existe um barco nessa posição!')
                continue

            tabuleiro[x][y] = 'B'
            barcos_colocados += 1

        except ValueError:
            enviar(cliente, 'ERRO: Entrada inválida. Digite dois números inteiros.')
        except OSError:
            print('Jogador desconectou durante posicionamento.')
            return False   # Sinaliza falha

    enviar(cliente, 'Barcos posicionados com sucesso! Aguardando o adversário...')
    return True


def processar_jogada(atacante_idx, defensor_idx, x, y):
    """
    Aplica o ataque do jogador 'atacante_idx' no tabuleiro do 'defensor_idx'.

    Retornos possíveis:
        'ACERTOU'            → barco destruído
        'ERROU'              → água
        'POSIÇÃO JÁ USADA'  → coordenada repetida (jogada desperdiçada)
    """
    alvo = tabuleiros[defensor_idx]

    if alvo[x][y] == 'B':
        alvo[x][y] = 'X'
        return 'ACERTOU'
    elif alvo[x][y] == '~':
        alvo[x][y] = 'O'
        return 'ERROU'
    else:
        return 'POSIÇÃO JÁ USADA'


def gerenciar_cliente(cliente, indice):
    """
    Thread responsável por gerenciar o turno de um jogador.
    Aguarda ser a vez do jogador, exibe os tabuleiros,
    lê o ataque e processa o resultado.
    """
    global turno, fim_jogo

    enviar(cliente, 'Bem-vindo ao Batalha Naval!')

    # Aguarda o outro jogador terminar o posicionamento.
    # A Barrier bloqueia aqui até que ambas as threads cheguem
    # a este ponto — garantindo que tabuleiros[0] e tabuleiros[1]
    # já existem antes de qualquer acesso.
    try:
        barreira.wait()
    except threading.BrokenBarrierError:
        enviar(cliente, 'Erro ao sincronizar jogadores. Encerrando.')
        return

    adversario = 1 - indice  # 0→1, 1→0

    enviar(cliente, '')
    enviar(cliente, '=== JOGO INICIADO ===')
    enviar(cliente, f'Você é o Jogador {indice + 1}: {nomes[indice]}')
    enviar(cliente, f'Seu adversário é: {nomes[adversario]}')

    while True:
        with lock:
            encerrado = fim_jogo
            minha_vez = (turno == indice)

        if encerrado:
            break

        if not minha_vez:
            # Não é o turno deste jogador; aguarda
            threading.Event().wait(0.1)
            continue

        # --- Turno deste jogador ---
        separador(cliente)
        enviar(cliente, f'>>> SUA VEZ, {nomes[indice].upper()}! <<<')

        enviar(cliente, '\nSEU TABULEIRO:')
        enviar(cliente, tabuleiro_texto(tabuleiros[indice]))

        enviar(cliente, '\nTABULEIRO INIMIGO:')
        enviar(cliente, tabuleiro_texto(tabuleiros[adversario], ocultar=True))

        enviar(cliente, '\nDigite linha e coluna do ataque (ex: 2 3):')

        try:
            dados = cliente.recv(1024).decode().strip()

            partes = dados.split()
            if len(partes) != 2:
                enviar(cliente, 'ERRO: Digite exatamente dois números (linha coluna).')
                continue

            x, y = int(partes[0]), int(partes[1])

            if not (0 <= x < TABULEIRO and 0 <= y < TABULEIRO):
                enviar(cliente, f'ERRO: Posição fora do tabuleiro! Use valores entre 0 e {TABULEIRO - 1}.')
                continue

            resultado = processar_jogada(indice, adversario, x, y)

            # Informa ambos os jogadores sobre o resultado
            enviar(cliente, f'Resultado: {resultado}')
            enviar(jogadores[adversario], f'\n{nomes[indice]} atacou ({x},{y}) → {resultado}')

            if resultado == 'POSIÇÃO JÁ USADA':
                enviar(cliente, 'Escolha outra posição.')
                continue  # Não consome o turno

            # Verifica condição de vitória
            with lock:
                if not barcos_restantes(tabuleiros[adversario]):
                    fim_jogo = True

            if fim_jogo:
                separador(cliente)
                enviar(cliente, 'VOCÊ VENCEU!')
                separador(jogadores[adversario])
                enviar(jogadores[adversario], 'VOCÊ PERDEU!')
                break

            # Passa o turno
            with lock:
                turno = adversario

        except ValueError:
            enviar(cliente, 'ERRO: Entrada inválida. Digite dois números inteiros.')
        except OSError:
            print(f'Jogador {nomes[indice]} desconectou durante o jogo.')
            with lock:
                fim_jogo = True
            break

    try:
        cliente.close()
    except OSError:
        pass

def iniciar_servidor():
    """
    Inicia o servidor TCP, aceita exatamente 2 jogadores,
    conduz o posicionamento de barcos e inicia as threads de jogo.
    """
    global turno, fim_jogo

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Permite reusar a porta imediatamente após reiniciar o servidor
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))
    servidor.listen(2)

    print(f'Servidor Batalha Naval iniciado em {HOST}:{PORT}')
    print('Aguardando 2 jogadores...')

    threads = []

    while len(jogadores) < 2:
        cliente, endereco = servidor.accept()
        print(f'Conexão recebida de {endereco}')

        # Solicita o nome do jogador
        enviar(cliente, 'Digite seu nome:')
        try:
            nome = cliente.recv(1024).decode().strip() or f'Jogador{len(jogadores)+1}'
        except OSError:
            nome = f'Jogador{len(jogadores)+1}'

        nomes.append(nome)
        jogadores.append(cliente)
        print(f'Jogador conectado: {nome}')

        # Fase de posicionamento (síncrona, antes de iniciar a thread)
        tabuleiro = criar_tabuleiro()
        sucesso = posicionar_barcos(cliente, tabuleiro)
        tabuleiros.append(tabuleiro)

        if not sucesso:
            print(f'{nome} desconectou antes de posicionar os barcos.')
            jogadores.remove(cliente)
            nomes.pop()
            tabuleiros.pop()
            continue

        # daemon=False: a thread não morre quando o processo principal termina
        thread = threading.Thread(
            target=gerenciar_cliente,
            args=(cliente, len(jogadores) - 1),
            daemon=False
        )
        thread.start()
        threads.append(thread)

    servidor.close()
    print('Dois jogadores conectados. Jogo em andamento!')

    # Bloqueia aqui até ambas as threads de jogo encerrarem
    for t in threads:
        t.join()

    print('Jogo encerrado.')


if __name__ == '__main__':
    iniciar_servidor()