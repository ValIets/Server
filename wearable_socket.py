import json
import queue
import threaded_server
import time

class WearableSocket(threaded_server.ThreadedSocket):
    log_prefix = '[WRBL]'
    
    def __init__(self, queue, parent_queue, connection, database_connection):
        threaded_server.ThreadedSocket.__init__(self, queue, parent_queue, connection, database_connection)
        
        self.connection.setblocking(False)
    
    def run(self):
        try:
            while True:
                if not self.queue.empty():
                    self.connection.sendall(str(self.queue.get()).encode('utf-8'))
                
                try:
                    msg = self.connection.recv(1024).decode('utf-8').strip()
                    
                    if not self.identifier:
                        self.identifier = json.loads(msg)['mac_address']
                    
                    if len(msg) > 0:
                        self.parent_queue.put(msg)
                except BlockingIOError:
                    time.sleep(0.01)
        except:
            self.connection.close()
