import socket
import threading

import networking


class Handler(threading.Thread):
    def __init__(self, socket):
        self.socket = socket
        super().__init__()

    def run(self):
        print("thread is running w socket", self.socket)
        while True:
            message = networking.recv_msg(self.socket)
            if message:
                print("received message", message)
                networking.send_msg(self.socket, {"m": "pong!", "c": message["c"]})
            else:
                print("no message received so ending loop")
                break


def main():
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_and_port = (socket.gethostname(), 8000)
    serversocket.bind(host_and_port)
    serversocket.listen(5)
    print("server listening on", host_and_port)

    while True:
        (clientsocket, address) = serversocket.accept()
        print("accepting connecting from", address)
        Handler(clientsocket).start()


if __name__ == "__main__":
    main()
