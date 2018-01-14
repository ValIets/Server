import base64
import hashlib
import json
import queue
import threaded_server
import time
import traceback
from utils import log

class WebAppSocket(threaded_server.ThreadedSocket):
    log_prefix = '[WBPP]'
    
    def __init__(self, queue, parent_queue, connection, database_connection):
        threaded_server.ThreadedSocket.__init__(self, queue, parent_queue, connection, database_connection)
        
        self.handshake()
        
        self.connection.setblocking(False)
    
    def run(self):
        self.send_residents()
        
        try:
            while True:
                if not self.queue.empty():
                    self.send(str(self.queue.get()))
                
                try:
                    msg_bytes = self.connection.recv(1024)
                    ( msg, opcode ) = self.decode_message(msg_bytes)
                    
                    if msg and len(msg) > 0:
                        if opcode == 0x09:
                            self.send(msg, 0x0A)
                        else:
                            self.parent_queue.put(msg)
                except BlockingIOError:
                    time.sleep(0.01)
        except:
            log(traceback.format_exc())
            self.connection.close()
    
    
    
    def handshake(self):
        data = self.connection.recv(1024).decode('utf-8')
        key = ''
        
        for line in data.split('\n'):
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
    
    def decode_message(self, message_bytes):
        if len(message_bytes) <= 1:
            return ( None, 0 )
        
        opcode = message_bytes[0] & 0b00001111
        
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
        
        return (''.join(characters), opcode )
    
    def send(self, message, opcode=1):
        message = str(message)
        
        send_bytes = []
        send_bytes.append(128 + opcode)
        
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
    
    
    
    def send_residents(self):
        residents = self.database_connection.get_all_residents()
        residents_array = []
        resident_dict = {}
        
        for resident in residents:
            wearable = self.database_connection.get_newest_wearable(resident[0])
            status = self.database_connection.get_status(resident[0])
            low_battery = False
            
            if not wearable is None:
                low_battery = (wearable[3] == 1)
            
            residents_array.append({ 'id': resident[0], 'firstname': resident[1], 'surname': resident[2], 'section': resident[3], 'address': resident[4], 'is_fallen': (status > 0), 'is_coming': (status == 2), 'low_battery': low_battery, 'birthday': resident[5].isoformat() })
        
        resident_dict['residents'] = residents_array
        json_data = json.dumps(resident_dict)
        
        self.send(json_data)
