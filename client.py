import socket
import threading
import sys

HOST = '127.0.0.1'  # Endereço do servidor (altere para IP remoto se necessário)
PORT = 5555

# Evento usado para sinalizar o encerramento das threads
encerrado = threading.Event()


def receber_mensagens(cliente):
    """
    Thread dedicada ao recebimento de mensagens do servidor.
    Exibe cada mensagem recebida no console.
    Encerra automaticamente quando a conexão é fechada.
    """
    while not encerrado.is_set():
        try:
            dados = cliente.recv(4096)

            if not dados:
                # Servidor encerrou a conexão
                print('\n[Conexão encerrada pelo servidor.]')
                encerrado.set()
                break

            # Exibe a mensagem recebida
            print(dados.decode(), end='', flush=True)

        except OSError:
            if not encerrado.is_set():
                print('\n[Erro na conexão com o servidor.]')
            encerrado.set()
            break


def main():
    """
    Função principal do cliente:
    1. Conecta ao servidor.
    2. Inicia thread de recebimento.
    3. Lê entrada do usuário e envia ao servidor.
    """
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        cliente.connect((HOST, PORT))
        print(f'Conectado ao servidor {HOST}:{PORT}')
        print('(Digite suas respostas e pressione Enter)\n')
    except ConnectionRefusedError:
        print(f'ERRO: Não foi possível conectar em {HOST}:{PORT}.')
        print('Verifique se o servidor está em execução.')
        sys.exit(1)

    # Inicia thread de recebimento como daemon (encerra com o programa)
    thread = threading.Thread(target=receber_mensagens, args=(cliente,), daemon=True)
    thread.start()

    # Loop de envio de mensagens
    try:
        while not encerrado.is_set():
            try:
                mensagem = input()
                if encerrado.is_set():
                    break
                cliente.sendall(mensagem.encode())
            except EOFError:
                # Fim de entrada padrão (ex: pipe ou Ctrl+D)
                break
    except KeyboardInterrupt:
        print('\n[Encerrando por solicitação do usuário.]')
    finally:
        encerrado.set()
        try:
            cliente.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        cliente.close()
        print('[Desconectado.]')


if __name__ == '__main__':
    main()
