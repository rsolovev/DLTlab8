import base64
import os

from Crypto import Random
from Crypto.Cipher import AES
import random
from peer_socket import PeerSocket

BLOCK_SIZE = 32
PADDING = '{'


def _unpad(s):
    return s[:-ord(s[len(s) - 1:])]


def _pad(s):
    return s + ((BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE))


def encrypt(key, raw):
    raw = _pad(raw)
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return base64.b64encode(iv + cipher.encrypt(raw.encode()))


def decrypt(key, enc):
    enc = base64.b64decode(enc)
    iv = enc[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return _unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')


if __name__ == "__main__":
    friendly_key, enemy_key = os.urandom(BLOCK_SIZE), os.urandom(BLOCK_SIZE)
    peers = [
        PeerSocket(('localhost', 6146), friendly_key),
        PeerSocket(('localhost', 7146), friendly_key),
        PeerSocket(('localhost', 8146), friendly_key),
        PeerSocket(('localhost', 9196), enemy_key),
        PeerSocket(('localhost', 9156), enemy_key)
    ]

    main_node = random.randint(0, len(peers)-1)
    votes = 0


    def greeting_wrapper(key):
        def greeting(sender_addr, message):
            decrypted = decrypt(key, message)
            if decrypted == "MESSAGE":
                print(str(sender_addr) + ' said ' + decrypted, " (raw: ", message, " )")
                return "OK"
            else:
                return main_node

        return greeting


    def response(message):
        global votes
        if str(message) == str(main_node):
            votes += 1
            print('Got response ' + str(message) + ' is the enemy')
        else:
            print('Got response ' + str(message) + ' is not the enemy')


    event = 'GREETING'

    for x in peers:
        x.on(event, greeting_wrapper(x.key))

    for x in peers:
        peers[main_node].send(x.addr, event, encrypt(peers[main_node].key, "MESSAGE"), response)
    if votes == 3:
        print("Primary node is the enemy, confirmed by", votes, "nodes")
