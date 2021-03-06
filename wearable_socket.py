import base64
import hashlib
import json
import queue
import threaded_server
import time
import traceback
from utils import log

class WearableSocket(threaded_server.ThreadedSocket):
    log_prefix = '[WRBL]'
    
    def __init__(self, queue, parent_queue, connection, database_connection):
        threaded_server.ThreadedSocket.__init__(self, queue, parent_queue, connection, database_connection)
        
        self.handshake_data = ''
        
        while not self.handshake():
            pass
        
        self.connection.setblocking(False)
    
    def run(self):
        try:
            while True:
                if not self.queue.empty():
                    self.send(str(self.queue.get()))
                
                try:
                    msg_bytes = self.connection.recv(1024)
                    msg = self.decode_message(msg_bytes)
                    
                    if msg and len(msg) > 0:
                        if not self.identifier:
                            try:
                                self.identifier = json.loads(msg)['mac_address']
                            except:
                                pass
                        
                        if msg == 'Ping!':
                            self.send('Pong!')
                        else:
                            self.parent_queue.put(msg)
                except BlockingIOError:
                    time.sleep(0.01)
        except:
            log(traceback.format_exc())
            self.connection.close()
    
    
    
    def handshake(self):
        self.handshake_data += self.connection.recv(1024).decode('utf-8')
        key = ''
        
        if len(self.handshake_data) < 4:
            return False
        
        for line in self.handshake_data.split('\n'):
            if line.startswith('Sec-WebSocket-Key:'):
                key = line.split(':', 1)[1].strip()
        
        key = key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
        key = hashlib.sha1(key.encode('ascii')).digest()
        key = base64.b64encode(key).decode('ascii')
        
        self.connection.sendall((
            'HTTP/1.1 101 Switching Protocols\n'
            'Upgrade: websocket\n'
            'Connection: Upgrade\n'
            'Sec-WebSocket-Accept: ' + key + '\n'
            '\n'
        ).encode('utf-8'))
        
        return True
    
    def decode_message(self, message_bytes):
        if len(message_bytes) <= 1:
            return
        
        message_length = message_bytes[1] & 127
        
        first_mask = 2
        if message_length == 126:
            first_mask = 4
        elif message_length == 127:
            first_mask = 10
        
        first_data = first_mask + 4
        
        masks = []
        for mask in message_bytes[first_mask:first_data]:
            masks.append(mask)
        
        characters = []
        for i in range(first_data, len(message_bytes)):
            characters.append(chr(message_bytes[i] ^ masks[(i - first_data) % 4]))
        
        return ''.join(characters)
    
    def send(self, message):
        message = str(message)
        
        send_bytes = []
        send_bytes.append(129)
        
        message_bytes = message.encode()
        message_length = len(message_bytes)
        
        if message_length < 126:
            send_bytes.append(message_length)
        elif message_length >= 126 and message_length < 65536:
            send_bytes.append(126)
            send_bytes.append((message_length >> 8) & 255)
            send_bytes.append(message_length & 255)
        else:
            send_bytes.append(127)
            send_bytes.append((message_length >> 56) & 255)
            send_bytes.append((message_length >> 48) & 255)
            send_bytes.append((message_length >> 40) & 255)
            send_bytes.append((message_length >> 32) & 255)
            send_bytes.append((message_length >> 24) & 255)
            send_bytes.append((message_length >> 16) & 255)
            send_bytes.append((message_length >> 8) & 255)
            send_bytes.append(message_length & 255)
        
        send_bytes = bytes(send_bytes)
        send_bytes = send_bytes + message_bytes
        
        self.connection.sendall(send_bytes)
