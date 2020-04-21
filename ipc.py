import socket
import threading


class IpcServer:
    def __init__(self):
        self._bind_address = 'localhost'
        self._port = 2400
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind((self._bind_address, self._port))
        self._socket.listen(3)
        self._thread = threading.Thread(target=self._run_server)

    def _run_server(self):
        self._running = True
        while True:
            client, addr = self._socket.accept()
            if not self._running:
                break
            print('CLIENT SOCKET: {} {}'.format(client, addr))
            print(client.recv(32))
            client.send(b'Hi\n')

    def start(self):
        self._thread.start()

    def stop(self):
        self._running = False

        # Make dummy connection to server to get out of blocking accept()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self._bind_address, self._port))
        s.close()

        self._thread.join()
