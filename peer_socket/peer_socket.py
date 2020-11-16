# first of all import the socket library 
import socket
import jsonpickle
from threading import Thread
from socket_message import SocketMessage


class PeerSocket:
    def __init__(self, addr, key, debug=False,):
        self.callbacks = {}
        self.debug = debug
        self.addr = addr
        self.sender_addr = ()
        self.key = key
        thread = Thread(target=self.runner, args=(self.addr,))
        thread.start()

    def __debug(self, msg):
        if self.debug:
            print(str(self.addr) + ': ' + msg)

    def runner(self, addr):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(addr)
        self.server.listen()
        while True:
            conn, addr = self.server.accept()
            buffer = conn.recv(1024)
            if len(buffer) > 0:
                json = buffer.decode('UTF-8')
                message = jsonpickle.decode(json)
                self.__debug('Got request ' + message.event + ' from peer ' + str(message.sender_addr) + '.')
                response = self.callbacks[message.event](message.sender_addr, message.payload)
                json = jsonpickle.encode(response)
                buffer = json.encode('UTF-8')
                conn.send(buffer)
            conn.close()

    def on(self, event, f):
        self.callbacks[event] = f

    def send(self, dest_addr, event, payload, callback=None):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(dest_addr)
        message = SocketMessage(self.addr, event, payload)
        json = jsonpickle.encode(message)
        buffer = json.encode('UTF-8')
        client.send(buffer)
        if callback is None:
            return
        buffer = client.recv(1024)
        if len(buffer) > 0:
            json = buffer.decode('UTF-8')
            message = jsonpickle.decode(json)
            self.__debug('Got response from peer ' + str(dest_addr) + '.')
            callback(message)