import socket
import time
import select

import networking


def build_ping_message(count):
    return {"cmd": "ping", "pingpong-counter": count}


class Client(object):
    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setblocking(False)
        try:
            s.connect(("localhost", 8000))
        except BlockingIOError:
            print("connection will complete async")

        self.server = networking.Messenger(s)
        self.server.queue_message(1, build_ping_message(count=0))
        self.server.queue_message(2, build_ping_message(count=100))

        while True:
            time.sleep(1)  # a nice sleep to make output easier to read

            timeout = 0.01  # in seconds
            ready_to_read, ready_to_write, in_error = select.select(
                [self.server.socket],
                [self.server.socket] if self.server.has_messages_to_send() else [],
                [self.server.socket],
                timeout,
            )

            if self.server.socket in in_error:
                print("Exiting due to socket being in error")
                return

            if self.server.socket in ready_to_write:
                try:
                    self.server.send_messages()
                except networking.MessengerConnectionBroken as e:
                    print("Handling send error by exiting:", e)
                    return

            if self.server.socket in ready_to_read:
                try:
                    for tid, message in self.server.read_messages():
                        self.handle_message(tid, message)
                except networking.MessengerBufferFullError as e:
                    print("Handling full buffer read error by exiting:", e)
                    return
                except networking.MessengerConnectionBroken as e:
                    print("Handling broken connection read error by exiting:", e)
                    return

        self.server.queue_message(tid, message)

    def handle_message(self, tid, message):
        if "cmd" not in message:
            print("unrecognized message, tid: {}  message: {}".format(tid, message))
            return
        cmd = message["cmd"]

        if cmd == "pong":
            count = message["pingpong-counter"]
            print("Received ping pong #{}! Trying {} now.".format(count, count + 1))
            self.server.queue_message(tid, build_ping_message(count + 1))
        elif cmd == "time":
            time = message["time"]
            print("Received server time broadcast! Time on server is {}".format(time))
        elif tid == 0 and "success" in message:
            # draconity is telling us whether a command we issued succeeded
            print("Received Draconity command result: success={}, cmd={}".format(message['success'], cmd))
        else:
            print("unrecognized message method:", method)


if __name__ == "__main__":
    Client().run()
