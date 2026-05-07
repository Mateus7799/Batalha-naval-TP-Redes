import socket
import threading
import sys

HOST = '127.0.0.1'
PORT = 5555

encerrado = threading.Event()


def receber_mensagens(cliente):
    while not encerrado.is_set():
        try:
            dados = cliente.recv(4096)

            if not dados:
                print('\n[Conexão encerrada pelo servidor.]')
                encerrado.set()
                break

            print(dados.decode(), end='', flush=True)

        except OSError:
            if not encerrado.is_set():
                print('\n[Erro na conexão com o servidor.]')
            encerrado.set()
            break


def main():
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        cliente.connect((HOST, PORT))
        print(f'Conectado ao servidor {HOST}:{PORT}')
        print('(Digite suas respostas e pressione Enter)\n')
    except ConnectionRefusedError:
        print(f'ERRO: Não foi possível conectar em {HOST}:{PORT}.')
        print('Verifique se o servidor está em execução.')
        sys.exit(1)

    thread = threading.Thread(target=receber_mensagens, args=(cliente,), daemon=True)
    thread.start()

    try:
        while not encerrado.is_set():
            try:
                mensagem = input()
                if encerrado.is_set():
                    break
                cliente.sendall(mensagem.encode())
            except EOFError:
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