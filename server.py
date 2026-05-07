import socket
import threading

HOST = '0.0.0.0'
PORT = 5555

TABULEIRO = 5        # Dimensão do tabuleiro (5x5)
QUANTIDADE_BARCOS = 3  # Barcos por jogador

lock = threading.Lock()

jogadores = []
nomes = []
tabuleiros = []
turno = 0
fim_jogo = False

barreira = threading.Barrier(2)

def criar_tabuleiro():
    return [['~' for _ in range(TABULEIRO)] for _ in range(TABULEIRO)]


def enviar(cliente, mensagem):
    try:
        cliente.sendall((mensagem + '\n').encode())
    except OSError:
        pass


def tabuleiro_texto(tabuleiro, ocultar=False):
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
    return any('B' in linha for linha in tabuleiro)


def separador(cliente):
    enviar(cliente, '-' * 30)


def posicionar_barcos(cliente, tabuleiro):
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
            return False

    enviar(cliente, 'Barcos posicionados com sucesso! Aguardando o adversário...')
    return True


def processar_jogada(atacante_idx, defensor_idx, x, y):
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
    global turno, fim_jogo

    enviar(cliente, 'Bem-vindo ao Batalha Naval!')
    try:
        barreira.wait()
    except threading.BrokenBarrierError:
        enviar(cliente, 'Erro ao sincronizar jogadores. Encerrando.')
        return

    adversario = 1 - indice

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
            threading.Event().wait(0.1)
            continue

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

            enviar(cliente, f'Resultado: {resultado}')
            enviar(jogadores[adversario], f'\n{nomes[indice]} atacou ({x},{y}) → {resultado}')

            if resultado == 'POSIÇÃO JÁ USADA':
                enviar(cliente, 'Escolha outra posição.')
                continue

            with lock:
                if not barcos_restantes(tabuleiros[adversario]):
                    fim_jogo = True

            if fim_jogo:
                separador(cliente)
                enviar(cliente, '🏆 VOCÊ VENCEU! Todos os barcos inimigos foram destruídos!')
                separador(jogadores[adversario])
                enviar(jogadores[adversario], '💀 VOCÊ PERDEU! Todos os seus barcos foram destruídos.')
                break

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
    global turno, fim_jogo

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))
    servidor.listen(2)

    print(f'Servidor Batalha Naval iniciado em {HOST}:{PORT}')
    print('Aguardando 2 jogadores...')

    threads = []

    while len(jogadores) < 2:
        cliente, endereco = servidor.accept()
        print(f'Conexão recebida de {endereco}')

        enviar(cliente, 'Digite seu nome:')
        try:
            nome = cliente.recv(1024).decode().strip() or f'Jogador{len(jogadores)+1}'
        except OSError:
            nome = f'Jogador{len(jogadores)+1}'

        nomes.append(nome)
        jogadores.append(cliente)
        print(f'Jogador conectado: {nome}')

        tabuleiro = criar_tabuleiro()
        sucesso = posicionar_barcos(cliente, tabuleiro)
        tabuleiros.append(tabuleiro)

        if not sucesso:
            print(f'{nome} desconectou antes de posicionar os barcos.')
            jogadores.remove(cliente)
            nomes.pop()
            tabuleiros.pop()
            continue

        thread = threading.Thread(
            target=gerenciar_cliente,
            args=(cliente, len(jogadores) - 1),
            daemon=False
        )
        thread.start()
        threads.append(thread)

    servidor.close()
    print('Dois jogadores conectados. Jogo em andamento!')

    for t in threads:
        t.join()

    print('Jogo encerrado.')


if __name__ == '__main__':
    iniciar_servidor()